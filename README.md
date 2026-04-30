# Personal Finance Management

A web app that links your bank accounts via **Stripe Financial Connections** and syncs your transaction history to a **Google Spreadsheet**. All secrets are stored encrypted in **AWS Parameter Store** — nothing sensitive ever touches your code or a file.

Syncs can be triggered manually with a single command, or run automatically every week via Windows Task Scheduler.

## How It Works

1. Open the web app and click **Connect Bank Account** — Stripe opens a secure modal to link your bank
2. Click **Sync Transactions to Google Sheets** — transactions are written to your spreadsheet and your account is saved for future syncs
3. From then on, run `bank-sync` in any terminal to pull the latest transactions, or let the weekly scheduler do it automatically

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
pip install -e .
```

> `pip install -e .` installs all dependencies and registers the `bank-sync` command globally.

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

Run these four commands, substituting your real values. All parameters are stored as **SecureString** (encrypted with the free AWS managed key):

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

# Store the entire service account JSON as a single encrypted parameter
aws ssm put-parameter \
  --name "/stripe-bank-sync/google-service-account-json" \
  --value file://service_account.json \
  --type SecureString
```

After storing them, delete `service_account.json` from your machine — it is no longer needed.

### 5. Connect your bank account (one time)

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000), click **Connect Bank Account**, then click **Sync Transactions to Google Sheets**. This links your bank and saves your account ID for all future syncs.

---

## Triggering a Sync

### Manual — run anytime from any terminal

```bash
bank-sync
```

Override the saved account with a specific one:

```bash
bank-sync --account-id acct_abc123
```

### Automatic — every Monday at 8:00 AM

Run once as Administrator to register the weekly job:

```powershell
.\setup_scheduler.ps1
```

After that, `bank-sync` runs automatically in the background every Monday. Logs are written to `sync_job.log`.

Other scheduler commands:

```powershell
Start-ScheduledTask -TaskName "StripeBankSync"   # run immediately
Get-ScheduledTask  -TaskName "StripeBankSync"    # check status
Unregister-ScheduledTask -TaskName "StripeBankSync"  # remove
```

---

## Project Structure

```
├── app.py                  # Flask web app & Stripe Financial Connections logic
├── sync_job.py             # bank-sync CLI command & sync logic
├── config.py               # AWS Parameter Store secret fetching (cached)
├── sheets.py               # Google Sheets writer
├── setup_scheduler.ps1     # Registers weekly Task Scheduler job
├── templates/
│   └── index.html          # Frontend UI with Stripe.js
├── pyproject.toml          # Installs bank-sync as a console command
├── requirements.txt
├── .env.example            # AWS credentials reference (local dev only)
└── .gitignore
```

## Security Notes

- All secrets live in AWS Parameter Store encrypted at rest — no `.env`, no JSON files on disk
- `service_account.json` is gitignored; delete it after uploading to Parameter Store
- Stripe handles all bank credential collection; your server never sees login details
- On AWS (EC2/Lambda/ECS), attach an IAM role with `ssm:GetParameter` — no credentials file needed at all
- Use test mode keys (`sk_test_`, `pk_test_`) during development
