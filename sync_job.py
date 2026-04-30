"""
CLI entry point — run `bank-sync` from any terminal to trigger an immediate sync.
Scheduled automatically every Monday at 8am when the web app is running.
"""
import sys
import logging
import click
import config
import sync as sync_module

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("sync_job.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


@click.command()
@click.option("--account-id", default=None, help="Override the saved linked account ID.")
def cli(account_id):
    """Pull bank transactions from Stripe and write them to Google Sheets."""
    if not config.is_setup_complete():
        log.error("App not configured. Open http://localhost:5000 and complete setup first.")
        sys.exit(1)

    log.info("Starting sync...")
    result = sync_module.run_sync(account_id=account_id)
    log.info(f"Done. {result['message']}")
    if result.get("url"):
        log.info(f"Spreadsheet: {result['url']}")


if __name__ == "__main__":
    cli()
