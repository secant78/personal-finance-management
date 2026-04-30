# Personal Finance Management

A web app that links your bank accounts via **Stripe Financial Connections** and syncs your transaction history to a **Google Spreadsheet**. All secrets are stored encrypted in **AWS Parameter Store** — nothing sensitive ever touches your code or a file.

## How It Works

1. Open the app in your browser
2. Click **Connect Bank Account** — Stripe opens a secure modal to link your bank
3. Click **Sync Transactions to Google Sheets** — all transactions are fetched and written to your spreadsheet

Each linked account gets its own tab in the spreadsheet with these columns:

| Transaction ID | Date | Description | Amount | Currency | Status | Category |
|---|---|---|---|---|---|---|

## Prerequisites

- Python 3.9+
- AWS CLI configured (`aws configure`)
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
3. Go to **Credentials → Create Credentials → Service Account**, download the JSON key
4. Create a blank Google Sheet
5. Share the sheet with the service account email (found in the JSON under `client_email`) with **Editor** access
6. Copy the spreadsheet ID from the URL: `https://docs.google.com/spreadsheets/d/`**`THIS_PART`**`/edit`

### 4. Store secrets in AWS Parameter Store

Run these four commands in your terminal, substituting your real values. All parameters are stored as **SecureString** (encrypted with the free AWS managed key):

```bash
aws ssm put-parameter \
  --name "/stripe-bank-sync/stripe-secret-key" \
  --value "sk_test_..." \
  --type SecureString

aws ssm put-parameter \
  --name "/stripe-bank-sync/stripe-publishable-key" \
  --value "pk_test_..." \
  --type SecureString

aws ssm put-parameter \
  --name "/stripe-bank-sync/google-spreadsheet-id" \
  --value "your_spreadsheet_id_here" \
  --type SecureString

# Store the entire service account JSON file as a single parameter
aws ssm put-parameter \
  --name "/stripe-bank-sync/google-service-account-json" \
  --value file://service_account.json \
  --type SecureString
```

After storing them, you can delete `service_account.json` from your machine — it is no longer needed.

### 5. Run

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Project Structure

```
├── app.py                  # Flask server & Stripe Financial Connections logic
├── config.py               # AWS Parameter Store secret fetching (cached)
├── sheets.py               # Google Sheets writer
├── templates/
│   └── index.html          # Frontend UI with Stripe.js
├── requirements.txt
├── .env.example            # AWS credentials reference (local dev only)
└── .gitignore
```

## Security Notes

- All secrets live in AWS Parameter Store encrypted at rest — no `.env`, no JSON files on disk
- `service_account.json` is gitignored; delete it after uploading to Parameter Store
- Stripe handles all bank credential collection; your server never sees login details
- On AWS (EC2/Lambda/ECS), attach an IAM role with `ssm:GetParameter` permission — no credentials file needed at all
- Use test mode keys (`sk_test_`, `pk_test_`) during development
