# Personal Finance Management

A web app that links your credit cards via **Stripe Financial Connections** and syncs your transaction history to a **Google Spreadsheet**. Secrets are stored encrypted in **Bitwarden** using the `bw` CLI — nothing sensitive ever touches your code or a plain file.

Each card gets its own tab in the spreadsheet. A **Master** tab consolidates all transactions across every card in one place.

Syncs can be triggered manually from the dashboard, or run automatically every Monday at 8 AM.

## How It Works

1. Run the app and open the dashboard
2. Click **+ Connect Account** — Stripe opens a secure modal to link your bank. Select all your credit cards at once
3. Click **Sync Now** — transactions are written to Google Sheets, one tab per card plus a Master tab
4. From then on, sync manually from the dashboard or let the weekly scheduler handle it

## Spreadsheet Layout

Each connected card gets its own tab named after the card (e.g., "Savor ••8505"). A **Master** tab combines all cards sorted newest first.

Every tab has these columns:

| Transaction ID | Date | Description | Amount | Currency | Status | Category | Card |
|---|---|---|---|---|---|---|---|

The **Category** column is auto-filled by matching the merchant description against known keywords (Gas, Fast Food, Dining, Grocery, Subscriptions, Health, Lodging, Transportation, Flights, Entertainment, Utilities/Phone, Fitness).

## Prerequisites

- Python 3.9+
- [Bitwarden CLI](https://bitwarden.com/help/cli/) (`bw`) installed and on your PATH
- A [Bitwarden](https://bitwarden.com) account (free tier works)
- A [Stripe account](https://stripe.com) with Financial Connections enabled (live mode, individual account)
- A Google Cloud project with the Sheets API enabled and a service account

## Setup

### 1. Clone and install

```bash
git clone https://github.com/secant78/personal-finance-management.git
cd personal-finance-management
pip install -r requirements.txt
```

### 2. Install the Bitwarden CLI

Download from [bitwarden.com/help/cli](https://bitwarden.com/help/cli/) and make sure `bw` is available in your terminal.

Verify:
```bash
bw --version
```

### 3. Get your Bitwarden API key

1. Log in to [vault.bitwarden.com](https://vault.bitwarden.com)
2. Go to **Account Settings → Security → API Key**
3. Note your **Client ID**, **Client Secret**, and **Master Password** — you'll enter these in the app setup form

### 4. Enable Stripe Financial Connections

1. Log in to your [Stripe Dashboard](https://dashboard.stripe.com)
2. Go to **Settings → Financial Connections** and activate the product
3. Copy your **Secret key** and **Publishable key** from **Developers → API keys**

> Use live mode keys for real transaction data. Stripe requires an individual or business account to use Financial Connections in live mode.

### 5. Set up Google Sheets

1. Go to [Google Cloud Console](https://console.cloud.google.com) → **APIs & Services → Library**
2. Search for and enable the **Google Sheets API**
3. Go to **Credentials → Create Credentials → Service Account**, then create a key and download the JSON file
4. Create a blank Google Sheet
5. Share the sheet with the service account email (found in the JSON under `client_email`) with **Editor** access
6. Copy the spreadsheet ID from the URL: `https://docs.google.com/spreadsheets/d/`**`THIS_PART`**`/edit`

### 6. Run the app and complete setup

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000). You'll be taken to the setup page. Fill in:

| Field | Where to find it |
|---|---|
| Bitwarden Server URL | Leave blank or enter `bitwarden.com` for the hosted service |
| Client ID | Bitwarden → Account Settings → API Key |
| Client Secret | Bitwarden → Account Settings → API Key |
| Master Password | Your Bitwarden master password |
| Stripe Secret Key | Stripe Dashboard → Developers → API keys |
| Stripe Publishable Key | Stripe Dashboard → Developers → API keys |
| Google Spreadsheet ID | From the Google Sheets URL |
| Service Account JSON | Upload the `.json` file downloaded from Google Cloud |

After submitting, the app stores all secrets in Bitwarden and redirects you to the dashboard.

### 7. Connect your bank accounts

On the dashboard, click **+ Connect Account**. A Stripe popup opens — log in to your bank and select **all** the credit cards you want to track. Each card is auto-named from Stripe's data (e.g., "Savor ••8505").

Click **+ Connect Account** again to add cards from a different bank.

To remove a bank connection, click **Remove** next to the institution name.

### 8. Sync transactions

Click **Sync Now** on the dashboard. Transactions are fetched for every connected card and written to Google Sheets — one tab per card, plus a Master tab with everything combined.

---

## Dashboard Overview

| Section | What it shows |
|---|---|
| Status cards | Live health check for Bitwarden, Stripe, Google Sheets, and bank connection |
| Connected Accounts | Each linked bank with its cards listed underneath |
| Transaction Sync | Last sync time, transaction count, link to spreadsheet, and next auto-sync time |
| Sync History | Last 10 syncs with status, count, trigger (manual/scheduled), and sheet link |

---

## Automatic Weekly Sync

The app runs a background scheduler that syncs automatically every **Monday at 8:00 AM** while the app is running. No extra setup needed — just keep `python app.py` running (e.g., as a Windows service or startup task).

---

## Project Structure

```
├── app.py              # Flask web app, routes, scheduler
├── sync.py             # Transaction fetching and sync orchestration
├── sheets.py           # Google Sheets writer (per-card tabs + Master tab)
├── categorize.py       # Keyword-based transaction categorizer
├── config.py           # Bitwarden CLI secret storage (get/put, cached)
├── templates/
│   ├── base.html       # Shared layout
│   ├── dashboard.html  # Main dashboard UI
│   └── setup.html      # First-run setup form
├── requirements.txt
└── .gitignore
```

## Security Notes

- All secrets are stored in Bitwarden as encrypted secure notes — no `.env` files, no plaintext on disk
- The only file written locally is `bootstrap.json`, which stores your Bitwarden API key so the app can unlock the vault on startup. Keep this file private and do not commit it
- Stripe handles all bank credential collection — your server never sees your bank login
- The service account JSON is uploaded once during setup and stored in Bitwarden; you can delete the local file after setup
