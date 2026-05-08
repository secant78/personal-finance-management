import datetime
import json

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

import config
from categorize import categorize

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_service():
    service_account_info = json.loads(config.get("/stripe-bank-sync/google-service-account-json"))
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def _spreadsheet_id() -> str:
    return config.get("/stripe-bank-sync/google-spreadsheet-id")


def _fmt_account_type(account_type: str) -> str:
    return {"credit_card": "Credit Card", "checking": "Checking", "savings": "Savings"}.get(account_type, account_type.replace("_", " ").title() if account_type else "")


def write_transactions_to_sheet(transactions: list, account_id: str, card_label: str = "", account_type: str = "") -> str:
    service = _get_service()
    sheet = service.spreadsheets()

    # Use a tab named after the card label or account id
    tab_name = (card_label or account_id)[:31]
    _ensure_tab(service, tab_name)

    header = ["Transaction ID", "Date", "Description", "Amount", "Currency", "Status", "Category", "Account Type", "Card"]
    rows = [header]

    fmt_type = _fmt_account_type(account_type)
    for txn in transactions:
        date = datetime.datetime.utcfromtimestamp(txn.transacted_at).strftime("%Y-%m-%d") if txn.transacted_at else ""
        amount = txn.amount / 100
        description = txn.description or ""
        rows.append([
            txn.id,
            date,
            description,
            amount,
            txn.currency.upper(),
            txn.status,
            categorize(description),
            fmt_type,
            card_label or account_id,
        ])

    sid = _spreadsheet_id()
    range_name = f"{tab_name}!A1"
    sheet.values().update(
        spreadsheetId=sid,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body={"values": rows},
    ).execute()

    # Bold the header row
    sheet_id = _get_sheet_id(service, tab_name)
    if sheet_id is not None:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sid,
            body={
                "requests": [{
                    "repeatCell": {
                        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                        "fields": "userEnteredFormat.textFormat.bold",
                    }
                }]
            },
        ).execute()

    return f"https://docs.google.com/spreadsheets/d/{sid}"


def write_master_sheet(all_transactions: list) -> None:
    """Write all transactions from all accounts into a single 'Master' tab, sorted by date desc."""
    service = _get_service()
    sid = _spreadsheet_id()
    tab_name = "Master"
    _ensure_tab(service, tab_name)

    header = ["Transaction ID", "Date", "Description", "Amount", "Currency", "Status", "Category", "Account Type", "Card"]
    rows = [header]

    sorted_txns = sorted(
        all_transactions,
        key=lambda x: (x[0].transacted_at or 0),
        reverse=True,
    )

    for txn, card_label, account_type in sorted_txns:
        date = datetime.datetime.utcfromtimestamp(txn.transacted_at).strftime("%Y-%m-%d") if txn.transacted_at else ""
        rows.append([
            txn.id,
            date,
            txn.description or "",
            txn.amount / 100,
            txn.currency.upper(),
            txn.status,
            categorize(txn.description or ""),
            _fmt_account_type(account_type),
            card_label,
        ])

    service.spreadsheets().values().update(
        spreadsheetId=sid,
        range=f"{tab_name}!A1",
        valueInputOption="USER_ENTERED",
        body={"values": rows},
    ).execute()

    sheet_id = _get_sheet_id(service, tab_name)
    if sheet_id is not None:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sid,
            body={
                "requests": [{
                    "repeatCell": {
                        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                        "fields": "userEnteredFormat.textFormat.bold",
                    }
                }]
            },
        ).execute()


def _ensure_tab(service, tab_name: str):
    sid = _spreadsheet_id()
    spreadsheet = service.spreadsheets().get(spreadsheetId=sid).execute()
    existing = [s["properties"]["title"] for s in spreadsheet["sheets"]]
    if tab_name not in existing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sid,
            body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
        ).execute()


def _get_sheet_id(service, tab_name: str):
    spreadsheet = service.spreadsheets().get(spreadsheetId=_spreadsheet_id()).execute()
    for s in spreadsheet["sheets"]:
        if s["properties"]["title"] == tab_name:
            return s["properties"]["sheetId"]
    return None
