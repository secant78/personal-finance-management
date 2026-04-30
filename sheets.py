import os
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.environ.get("GOOGLE_SPREADSHEET_ID")


def _get_service():
    creds = Credentials.from_service_account_file(
        os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"],
        scopes=SCOPES,
    )
    return build("sheets", "v4", credentials=creds)


def write_transactions_to_sheet(transactions: list, account_id: str) -> str:
    service = _get_service()
    sheet = service.spreadsheets()

    # Use a tab named after the account id, create it if it doesn't exist
    tab_name = account_id[:31]  # Sheet tab names are limited to 31 chars
    _ensure_tab(service, tab_name)

    header = ["Transaction ID", "Date", "Description", "Amount", "Currency", "Status", "Category"]
    rows = [header]

    for txn in transactions:
        date = datetime.datetime.utcfromtimestamp(txn.transacted_at).strftime("%Y-%m-%d") if txn.transacted_at else ""
        # amount is in cents; negative = debit, positive = credit
        amount = txn.amount / 100
        rows.append([
            txn.id,
            date,
            txn.description or "",
            amount,
            txn.currency.upper(),
            txn.status,
            ", ".join(txn.get("category", []) or []),
        ])

    range_name = f"{tab_name}!A1"
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body={"values": rows},
    ).execute()

    # Bold the header row
    sheet_id = _get_sheet_id(service, tab_name)
    if sheet_id is not None:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
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

    return f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"


def _ensure_tab(service, tab_name: str):
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    existing = [s["properties"]["title"] for s in spreadsheet["sheets"]]
    if tab_name not in existing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
        ).execute()


def _get_sheet_id(service, tab_name: str):
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    for s in spreadsheet["sheets"]:
        if s["properties"]["title"] == tab_name:
            return s["properties"]["sheetId"]
    return None
