# splitwise-updates

## Splitwise expense report

Pulls your Splitwise expenses and summarizes **your share** by category (not what you paid). It also provides a high-level summary of your total share vs what you paid, grouped by currency.

**Example output**

```
Date range: 2026-01-01  →  2026-01-31

SUMMARY (non-payment expenses only)
Currency  My total share  Total I paid
--------  --------------  ------------
USD       238.50          120.00

CATEGORY TOTALS (by my share)
Currency  Category     My share
--------  -----------  --------
USD       Groceries    140.00
USD       Dining       70.50
USD       Utilities    28.00
```

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### How to use

**Local run (default current month):**

```bash
export SPLITWISE_TOKEN="your_api_key_here"
python splitwise_expense_report.py
```

**Custom date range:**

```bash
python splitwise_expense_report.py --dated-after 2024-01-01 --dated-before 2024-01-31
```

**Trigger via Telegram (requires Cloudflare Worker setup below):**

```
/report --dated-after 2024-01-01 --dated-before 2024-01-31 --group-id 123456 --currency USD
```

### Options

- `--token`: Splitwise bearer token (or set `SPLITWISE_TOKEN`).
- `--group-id`: Optional group filter.
- `--dated-after` / `--dated-before`: Date filters in `YYYY-MM-DD` (defaults to current month).
- `--currency`: Currency label for display.

### Telegram commands (Cloudflare Worker, free)

This lets you send `/report` commands directly in Telegram and receive the report back.

1. Create a GitHub personal access token (classic) with `repo` and `workflow` scopes.
2. Deploy the Cloudflare Worker at `worker/telegram_worker.js`.
3. Add GitHub **Repository Secrets** (Repo → Settings → Secrets and variables → Actions):
   - `SPLITWISE_TOKEN` (Splitwise API key)
   - `WORKER_URL` (Cloudflare Worker URL)
   - `WORKER_TOKEN` (random secret you choose)
   - `CLOUDFLARE_API_TOKEN` (Cloudflare API token)
   - `CLOUDFLARE_ACCOUNT_ID` (Cloudflare dashboard → Account ID)
   - `CLOUDFLARE_WORKER_NAME` (your Worker name)
4. In your Worker settings, add these environment variables:
   - `TELEGRAM_BOT_TOKEN` (from @BotFather)
   - `GITHUB_TOKEN` (GitHub PAT with repo + workflow scopes)
   - `GITHUB_OWNER` (your GitHub username)
   - `GITHUB_REPO` (your repo name)
   - `GITHUB_WORKFLOW_FILE` (e.g., `splitwise-expense-report.yml`)
   - `GITHUB_REF` (optional, default `main`)
   - `ALLOWED_TELEGRAM_USERNAME` (your Telegram username)
   - `WORKER_TOKEN` (same value as GitHub secret)
5. Set the Telegram webhook to your Worker URL:
   ```
   https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=<WORKER_URL>
   ```

Command format:

```
/report [args...]
```

Example:

```
/report --dated-after 2024-01-01 --dated-before 2024-01-31 --group-id 123456 --currency USD
```

If you omit args, it defaults to the current month.

Note: GitHub Actions picks up workflows automatically once the `.github/workflows` file is pushed to your repo.

**Architecture (Telegram → GitHub Actions)**

```
Telegram /report
      │
      ▼
Cloudflare Worker (auth + webhook)
      │
      ▼
GitHub Actions (runs splitwise_expense_report.py)
      │
      ▼
Cloudflare Worker (callback)
      │
      ▼
Telegram response
```
