import json
import os
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
import config
import sync as sync_module

app = Flask(__name__)
app.secret_key = os.urandom(24)

SYNC_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "sync_history.json")


# ---------------------------------------------------------------------------
# Sync history helpers
# ---------------------------------------------------------------------------

def _load_history() -> list:
    if os.path.exists(SYNC_HISTORY_FILE):
        with open(SYNC_HISTORY_FILE) as f:
            return json.load(f)
    return []


def _append_history(entry: dict):
    history = _load_history()
    history.insert(0, entry)
    with open(SYNC_HISTORY_FILE, "w") as f:
        json.dump(history[:50], f, indent=2)


# ---------------------------------------------------------------------------
# Scheduled job
# ---------------------------------------------------------------------------

def _scheduled_sync():
    if not config.is_setup_complete():
        return
    try:
        result = sync_module.run_sync()
        _append_history({
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "status": "success",
            "count": result["count"],
            "url": result["url"],
            "trigger": "scheduled",
        })
    except Exception as exc:
        _append_history({
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "status": "error",
            "error": str(exc),
            "trigger": "scheduled",
        })


scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(_scheduled_sync, "cron", day_of_week="mon", hour=8, id="weekly_sync")
scheduler.start()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return redirect(url_for("dashboard") if config.is_setup_complete() else url_for("setup"))


@app.route("/setup", methods=["GET"])
def setup():
    return render_template("setup.html", updating=False)


@app.route("/setup", methods=["POST"])
def setup_post():
    vaultwarden_url  = request.form.get("vaultwarden_url", "").strip()
    bw_client_id     = request.form.get("bw_client_id", "").strip()
    bw_client_secret = request.form.get("bw_client_secret", "").strip()
    bw_password      = request.form.get("bw_password", "").strip()
    stripe_secret    = request.form.get("stripe_secret_key", "").strip()
    stripe_pub       = request.form.get("stripe_publishable_key", "").strip()
    spreadsheet_id   = request.form.get("google_spreadsheet_id", "").strip()
    sa_file = request.files.get("service_account_json")

    if not all([vaultwarden_url, bw_client_id, bw_client_secret, bw_password,
                stripe_secret, stripe_pub, spreadsheet_id, sa_file and sa_file.filename]):
        return render_template("setup.html", updating=False, error="All fields are required.")

    try:
        sa_json = sa_file.read().decode("utf-8")
        json.loads(sa_json)
    except Exception:
        return render_template("setup.html", updating=False, error="Service account file is not valid JSON.")

    try:
        config.save_bootstrap(vaultwarden_url, bw_client_id, bw_client_secret, bw_password)
        config.put("/stripe-bank-sync/stripe-secret-key",          stripe_secret)
        config.put("/stripe-bank-sync/stripe-publishable-key",     stripe_pub)
        config.put("/stripe-bank-sync/google-spreadsheet-id",      spreadsheet_id)
        config.put("/stripe-bank-sync/google-service-account-json", sa_json)
    except Exception as exc:
        return render_template("setup.html", updating=False, error=f"Could not save credentials: {exc}")

    return redirect(url_for("dashboard"))


@app.route("/settings", methods=["GET"])
def settings():
    return render_template("setup.html", updating=True)


@app.route("/dashboard")
def dashboard():
    if not config.is_setup_complete():
        return redirect(url_for("setup"))

    stripe_pub = None
    account_id = None
    vault_ok = stripe_ok = sheets_ok = bank_ok = False

    try:
        vault_ok = True  # bootstrap.json exists (checked above)
        stripe_pub = config.get("/stripe-bank-sync/stripe-publishable-key")
        config.get("/stripe-bank-sync/stripe-secret-key")
        stripe_ok = True
        config.get("/stripe-bank-sync/google-service-account-json")
        config.get("/stripe-bank-sync/google-spreadsheet-id")
        sheets_ok = True
        account_id = config.get("/stripe-bank-sync/linked-account-id")
        bank_ok = True
    except Exception:
        pass

    history = _load_history()

    return render_template(
        "dashboard.html",
        stripe_publishable_key=stripe_pub,
        account_id=account_id,
        history=history[:10],
        last_sync=history[0] if history else None,
        vault_ok=vault_ok,
        stripe_ok=stripe_ok,
        sheets_ok=sheets_ok,
        bank_ok=bank_ok,
        next_run=scheduler.get_job("weekly_sync").next_run_time,
    )


@app.route("/create-fc-session", methods=["POST"])
def create_fc_session():
    import stripe
    stripe.api_key = config.get("/stripe-bank-sync/stripe-secret-key")

    # Reuse existing customer or create one for this personal account
    try:
        customer_id = config.get("/stripe-bank-sync/stripe-customer-id")
    except KeyError:
        customer = stripe.Customer.create(name="Personal Finance")
        customer_id = customer.id
        config.put("/stripe-bank-sync/stripe-customer-id", customer_id)

    session = stripe.financial_connections.Session.create(
        account_holder={"type": "customer", "customer": customer_id},
        permissions=["transactions", "balances", "ownership"],
    )
    return jsonify({"client_secret": session.client_secret})


@app.route("/save-account", methods=["POST"])
def save_account():
    data = request.get_json()
    account_id = data.get("account_id")
    if not account_id:
        return jsonify({"error": "account_id required"}), 400
    config.put("/stripe-bank-sync/linked-account-id", account_id)
    return jsonify({"ok": True})


@app.route("/sync", methods=["POST"])
def sync():
    try:
        result = sync_module.run_sync()
        _append_history({
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "status": "success",
            "count": result["count"],
            "url": result["url"],
            "trigger": "manual",
        })
        return jsonify(result)
    except Exception as exc:
        import traceback
        app.logger.error("Sync failed: %s", traceback.format_exc())
        return jsonify({"error": f"{type(exc).__name__}: {exc}"}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=False)
