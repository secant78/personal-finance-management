import stripe
import config
from sheets import write_transactions_to_sheet


def _sync_one(account_id: str, card_label: str) -> dict:
    stripe.financial_connections.Account.refresh_account(
        account_id,
        features=["transactions"],
    )

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
        return {"count": 0, "url": None}

    url = write_transactions_to_sheet(transactions, account_id, card_label=card_label)
    return {"count": len(transactions), "url": url}


def run_sync_all(account_ids: list = None, labels: dict = None) -> dict:
    stripe.api_key = config.get("/stripe-bank-sync/stripe-secret-key")
    labels = labels or {}

    if not account_ids:
        account_ids = [config.get("/stripe-bank-sync/linked-account-id")]

    total_count = 0
    last_url = None

    for account_id in account_ids:
        result = _sync_one(account_id, labels.get(account_id, ""))
        total_count += result["count"]
        if result["url"]:
            last_url = result["url"]

    return {
        "count": total_count,
        "url": last_url,
        "message": f"Synced {total_count} transactions across {len(account_ids)} account(s).",
    }


# Keep old single-account entry point for backward compat
def run_sync(account_id: str = None, labels: dict = None) -> dict:
    stripe.api_key = config.get("/stripe-bank-sync/stripe-secret-key")
    if not account_id:
        account_id = config.get("/stripe-bank-sync/linked-account-id")
    result = _sync_one(account_id, (labels or {}).get(account_id, ""))
    return {**result, "message": f"Synced {result['count']} transactions."}
