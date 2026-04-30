"""
Weekly cron job — fetches bank transactions and writes them to Google Sheets.
Run directly: python sync_job.py
Scheduled via Windows Task Scheduler using setup_scheduler.ps1
"""
import sys
import logging
import stripe
import config
from sheets import write_transactions_to_sheet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("sync_job.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def fetch_transactions(account_id: str) -> list:
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

    return transactions


def run():
    stripe.api_key = config.get("/stripe-bank-sync/stripe-secret-key")
    account_id = config.get("/stripe-bank-sync/linked-account-id")

    log.info(f"Starting weekly sync for account {account_id}")

    transactions = fetch_transactions(account_id)

    if not transactions:
        log.info("No transactions found — nothing to write.")
        return

    url = write_transactions_to_sheet(transactions, account_id)
    log.info(f"Synced {len(transactions)} transactions → {url}")


if __name__ == "__main__":
    run()
