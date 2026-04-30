# Personal Finance Management

A web app that links your bank accounts via **Stripe Financial Connections** and syncs your transaction history to a **Google Spreadsheet**.

## How It Works

1. Open the app in your browser
2. Click **Connect Bank Account** — Stripe opens a secure modal to link your bank
3. Click **Sync Transactions to Google Sheets** — all transactions are fetched and written to your spreadsheet

Each linked account gets its own tab in the spreadsheet with these columns:

| Transaction ID | Date | Description | Amount | Currency | Status | Category |
|---|---|---|---|---|---|---|

## Prerequisites

- Python 3.9+
- A [Stripe account](https://stripe.com) with Financial Connections enabled
- A Google Cloud project with the Sheets API enabled

## Setup

### 1. Clone and install

```bash
git clone https://github.com/secant78/personal-finance-management.git
cd personal-finance-management
pip install -r requirements.txt
```

### 2. Enable Stripe Financial Connections

1. Log in to your [Stripe Dashboard](https://dashboard.stripe.com)
2. Go to **Settings → Financial Connections** and activate the product
3. Copy your **Secret key** and **Publishable key** from **Developers → API keys**

### 3. Set up Google Sheets

1. Go to [Google Cloud Console](https://console.cloud.google.com) → **APIs & Services → Library**
2. Enable the **Google Sheets API**
3. Go to **Credentials → Create Credentials → Service Account**, then download the JSON key and save it as `service_account.json` in the project root
4. Create a blank Google Sheet
5. Share the sheet with the service account email (found inside `service_account.json` under `client_email`) with **Editor** access
6. Copy the spreadsheet ID from the URL: `https://docs.google.com/spreadsheets/d/`**`THIS_PART`**`/edit`

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
```

### 5. Run

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Project Structure

```
├── app.py                  # Flask server & Stripe Financial Connections logic
├── sheets.py               # Google Sheets writer
├── templates/
│   └── index.html          # Frontend UI with Stripe.js
├── requirements.txt
├── .env.example
└── .gitignore
```

## Security Notes

- Your `.env` and `service_account.json` are excluded from version control via `.gitignore` — never commit them
- Stripe handles all bank credential collection; your server never sees login details
- Use test mode keys (`sk_test_`, `pk_test_`) during development
