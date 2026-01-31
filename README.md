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

### Run

```bash
export SPLITWISE_TOKEN="your_api_key_here"
python splitwise_expense_report.py --group-id 123456 --currency USD
```

### Options

- `--token`: Splitwise bearer token (or set `SPLITWISE_TOKEN`).
- `--group-id`: Optional group filter.
- `--dated-after` / `--dated-before`: Date filters in `YYYY-MM-DD` (defaults to current month).
- `--currency`: Currency label for display.

### Trigger from your phone

There are two ways to trigger the report:

1. **GitHub app (manual run)** — open the repo in the GitHub app → **Actions → Splitwise Expense Report** → **Run workflow**.
2. **Telegram command** — use the Cloudflare Worker setup below and send `/report` in Telegram.

> If you only use GitHub app, you don’t need the Cloudflare Worker.

### Telegram commands (Cloudflare Worker, free)

This lets you send `/report` commands directly in Telegram and receive the report back.

1. Create a GitHub personal access token (classic) with `repo` and `workflow` scopes.
2. Deploy the Cloudflare Worker at `worker/telegram_worker.js`.
3. In your Worker settings, add these environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `GITHUB_TOKEN`
   - `GITHUB_OWNER` (e.g., `your-username`)
   - `GITHUB_REPO` (e.g., `splitwise-updates`)
   - `GITHUB_WORKFLOW_FILE` (e.g., `splitwise-expense-report.yml`)
   - `GITHUB_REF` (optional, default `main`)
   - `ALLOWED_TELEGRAM_USERNAME` (set to your Telegram username)
   - `WORKER_TOKEN` (shared secret used by GitHub Actions)
4. Set the Telegram webhook to your Worker URL:
   ```
   https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=<WORKER_URL>
   ```

Command format:
```
/report 2024-01-01 2024-01-31 123456 USD
```
- Dates are optional (defaults to current month).
- `group_id` and `currency` are optional.

Note: GitHub Actions picks up workflows automatically once the `.github/workflows` file is pushed to your repo.