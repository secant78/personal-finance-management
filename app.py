import boto3
import stripe
from flask import Flask, render_template, request, jsonify
import config
from sheets import write_transactions_to_sheet

app = Flask(__name__)
stripe.api_key = config.get("/stripe-bank-sync/stripe-secret-key")


def _save_account_id(account_id: str):
    boto3.client("ssm", region_name="us-east-1").put_parameter(
        Name="/stripe-bank-sync/linked-account-id",
        Value=account_id,
        Type="String",
        Overwrite=True,
    )


@app.route("/")
def index():
    return render_template("index.html", stripe_publishable_key=config.get("/stripe-bank-sync/stripe-publishable-key"))


@app.route("/create-session", methods=["POST"])
def create_session():
    """Create a Financial Connections session and return the client secret."""
    session = stripe.financial_connections.Session.create(
        account_holder={"type": "individual"},
        permissions=["transactions", "balances", "ownership"],
    )
    return jsonify({"client_secret": session.client_secret})


@app.route("/sync", methods=["POST"])
def sync():
    """Fetch transactions for all linked accounts and write them to Google Sheets."""
    data = request.get_json()
    account_id = data.get("account_id")

    if not account_id:
        return jsonify({"error": "account_id is required"}), 400

    _save_account_id(account_id)

    # Refresh transactions so we get the latest data
    stripe.financial_connections.Account.refresh_account(
        account_id,
        features=["transactions"],
    )

    # Paginate through all transactions
    transactions = []
    has_more = True
    starting_after = None

    while has_more:
        params = {"account": account_id, "limit": 100}
        if starting_after:
            params["starting_after"] = starting_after

        page = stripe.financial_connections.Transaction.list(**params)
        transactions.extend(page.data)
        has_more = page.has_more
        if has_more:
            starting_after = page.data[-1].id

    if not transactions:
        return jsonify({"message": "No transactions found.", "count": 0})

    spreadsheet_url = write_transactions_to_sheet(transactions, account_id)
    return jsonify({"message": f"Synced {len(transactions)} transactions.", "count": len(transactions), "spreadsheet_url": spreadsheet_url})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
