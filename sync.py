import stripe

import config
from sheets import write_master_sheet, write_transactions_to_sheet


def _fetch_transactions(account_id: str) -> list:
    try:
        stripe.financial_connections.Account.refresh_account(
            account_id,
            features=["transactions"],
        )
    except stripe.error.InvalidRequestError as e:
        if "refresh is still pending" in str(e):
            pass
        else:
            raise

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

    return transactions


def run_sync_all(account_ids: list = None, labels: dict = None) -> dict:
    stripe.api_key = config.get("/stripe-bank-sync/stripe-secret-key")
    labels = labels or {}

    if not account_ids:
        account_ids = [config.get("/stripe-bank-sync/linked-account-id")]

    all_transactions = []  # [(txn, card_label), ...]
    total_count = 0
    last_url = None

    for account_id in account_ids:
        card_label = labels.get(account_id, account_id)
        txns = _fetch_transactions(account_id)
        if txns:
            url = write_transactions_to_sheet(txns, account_id, card_label=card_label)
            last_url = url
            total_count += len(txns)
            all_transactions.extend((t, card_label) for t in txns)

    if all_transactions:
        write_master_sheet(all_transactions)

    return {
        "count": total_count,
        "url": last_url,
        "message": f"Synced {total_count} transactions across {len(account_ids)} account(s).",
    }

