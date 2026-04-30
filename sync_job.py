"""
Usage:
  bank-sync          # pull transactions into Google Sheets now
  bank-sync --help   # show options

Scheduled automatically every Monday at 8am via setup_scheduler.ps1
"""
import sys
import logging
import click
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


@click.command()
@click.option("--account-id", default=None, help="Stripe Financial Connections account ID. Defaults to the saved linked account.")
def cli(account_id):
    """Pull bank transactions from Stripe and write them to Google Sheets."""
    stripe.api_key = config.get("/stripe-bank-sync/stripe-secret-key")

    if not account_id:
        account_id = config.get("/stripe-bank-sync/linked-account-id")

    log.info(f"Syncing account {account_id} ...")
    transactions = fetch_transactions(account_id)

    if not transactions:
        log.info("No transactions found — nothing to write.")
        return

    url = write_transactions_to_sheet(transactions, account_id)
    log.info(f"Done. Synced {len(transactions)} transactions → {url}")


if __name__ == "__main__":
    cli()
