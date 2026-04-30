import stripe
import config
from sheets import write_transactions_to_sheet


def run_sync(account_id: str = None) -> dict:
    stripe.api_key = config.get("/stripe-bank-sync/stripe-secret-key")

    if not account_id:
        account_id = config.get("/stripe-bank-sync/linked-account-id")

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
        return {"count": 0, "url": None, "message": "No transactions found."}

    url = write_transactions_to_sheet(transactions, account_id)
    return {"count": len(transactions), "url": url, "message": f"Synced {len(transactions)} transactions."}
