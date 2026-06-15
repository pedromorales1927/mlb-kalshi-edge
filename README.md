# MLB Kalshi Edge Platform

Production-ready MLB expected value analytics for identifying positive expected value opportunities versus Kalshi MLB market prices.

This is not a winner-picking app. It estimates true MLB game outcome probabilities, compares them with Kalshi implied probabilities, applies risk controls, and sends a daily report.

## Architecture

Recommended deployment:

- **Dashboard:** Next.js on Vercel.
- **Database:** Supabase PostgreSQL.
- **Automation:** GitHub Actions daily Python worker.
- **Email:** SendGrid.
- **ML:** Python, scikit-learn baseline, XGBoost primary model when installed.

Heavy Python dependencies are intentionally kept out of Vercel Functions. Vercel serves the dashboard and lightweight API routes; GitHub Actions runs the data/model/report pipeline every morning.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full diagram and design decisions.

## Features

- Pulls MLB schedule, standings, starters, and game context.
- Supports Kalshi API integration and CSV price fallback.
- Builds a game-level feature dataset.
- Generates home and away win probabilities.
- Calculates edge, expected value, confidence, fractional Kelly units, and exposure caps.
- Filters picks by edge, confidence, and confirmed starting pitchers.
- Stores predictions, prices, picks, results, model runs, bankroll ledger, and email reports.
- Sends a daily mobile-friendly SendGrid email with CSV and HTML attachments.
- Displays top bets, full board, model performance, bankroll, and backtest sections in a Vercel dashboard.

## Project Structure

```text
app/                         Next.js dashboard and API routes
database/schema.sql          Supabase PostgreSQL schema
docs/                        Architecture and roadmap
python/mlb_kalshi/           Python data, ML, betting, DB, and reporting package
scripts/run_daily.py         Daily automated worker entry point
scripts/train_model.py       Historical model training entry point
.github/workflows/           GitHub Actions automation
tests/                       Unit tests for betting and bankroll logic
```

## Supabase Setup

1. Create a Supabase project.
2. Open the SQL editor.
3. Run [database/schema.sql](database/schema.sql).
4. Copy your project URL and service role key.
5. Store the service role key only in server-side environments: Vercel environment variables and GitHub Actions secrets.

## Environment Variables

Copy `.env.example` to `.env.local` for Vercel local development. The Python worker reads `.env` and `.env.local`, so the same local file works for dashboard and worker testing. Configure the production values in Vercel and GitHub Actions secrets/vars.

Required:

- `NEXT_PUBLIC_SUPABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SENDGRID_API_KEY`
- `REPORT_EMAIL_FROM`
- `REPORT_EMAIL_TO`
- `ALERT_EMAIL_TO`

Optional:

- `KALSHI_API_BASE`
- `KALSHI_CSV_PATH`
- `LOCAL_TIMEZONE`
- `DEFAULT_BANKROLL_UNITS`
- `FRACTIONAL_KELLY`
- `FIXED_UNIT_SIZE`
- `SIZING_STRATEGY`
- `MAX_BET_UNITS`
- `MAX_DAILY_EXPOSURE_UNITS`
- `MINIMUM_EDGE`
- `MINIMUM_CONFIDENCE`
- `REQUIRE_CONFIRMED_STARTERS`
- `MODEL_ARTIFACT_PATH`
- `CRON_SECRET`

## Local Development

Install frontend dependencies:

```bash
npm install
```

Run the dashboard:

```bash
npm run dev
```

Install Python dependencies:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run the daily worker:

```bash
PYTHONPATH=python python scripts/run_daily.py
```

Run a specific slate:

```bash
PYTHONPATH=python python scripts/run_daily.py --date 2026-06-14
```

## Vercel Deployment

1. Import this repo into Vercel.
2. Set the environment variables from `.env.example`.
3. Deploy.
4. Confirm `/api/health` returns `ok: true`.

The included `vercel.json` defines a lightweight cron smoke check at `0 14 * * *`. The production ML workflow runs in GitHub Actions.

## GitHub Actions Setup

Add these repository secrets:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SENDGRID_API_KEY`
- `REPORT_EMAIL_FROM`
- `REPORT_EMAIL_TO`
- `ALERT_EMAIL_TO`

Add repository variables for tunable risk settings:

- `KALSHI_API_BASE`
- `DEFAULT_BANKROLL_UNITS`
- `FRACTIONAL_KELLY`
- `FIXED_UNIT_SIZE`
- `SIZING_STRATEGY`
- `MAX_BET_UNITS`
- `MAX_DAILY_EXPOSURE_UNITS`
- `MINIMUM_EDGE`
- `MINIMUM_CONFIDENCE`
- `REQUIRE_CONFIRMED_STARTERS`

Optional repository secret:

- `KALSHI_CSV_PATH`, only if the workflow runner has access to that file path. For most hosted GitHub Actions deployments, prefer live API pricing or commit a non-secret CSV fixture for testing.

The workflow runs daily at `14:00 UTC`, which corresponds to 9:00 AM America/Chicago during daylight saving time. Adjust the cron to `15:00 UTC` during standard time if you require exact 9:00 AM Central delivery year-round, or run the workflow hourly with a timezone guard.

## Kalshi Prices

The worker first tries the configured Kalshi API path. Because sports market naming can vary, CSV fallback is supported.

CSV columns:

```csv
away_team,home_team,side,yes_price_cents,market_ticker,event_ticker,volume,open_interest
BOS,NYY,home,50,KXMLB...,KXMLB...,1000,500
```

`side` must be `home` or `away`. Prices are cents from 1 to 99.

## Daily Email

Subject:

```text
MLB Kalshi Edge Report - YYYY-MM-DD
```

The email includes:

- Top 5 bets today.
- All qualifying bets.
- No bet games.
- Model performance summary.
- Bankroll recommendations.
- CSV and HTML attachments.

Failure alerts include timestamp, failed step, and error details.

## Modeling

Train a model from a user-supplied historical game-level CSV:

```bash
PYTHONPATH=python python scripts/train_model.py --input historical_features.csv --output artifacts/model.joblib --model xgboost
```

Expected historical dataset fields:

- `game_date`
- `home_win`
- Feature columns from `FeatureBuilder.feature_columns()`

The trainer uses:

- Time-ordered split.
- Logistic regression baseline.
- XGBoost primary model when installed.
- Probability calibration.
- Accuracy, ROC AUC, log loss, and Brier score.

If no artifact exists, daily inference uses a transparent baseline formula so the automation remains operational while historical backfill is being built.

## Betting Rules

Default recommendation filters:

- Edge >= 4%.
- Confidence score >= configured threshold.
- Starting pitchers confirmed.
- Daily exposure <= configured cap.
- Per-bet units <= configured cap.

Sizing options:

- Fractional Kelly.
- Fixed unit.

## Backtesting

Backtesting is supported by storing historical predictions, Kalshi snapshots, picks, and results in Supabase. The dashboard has backtest sections for:

- ROI by season.
- ROI by edge bucket.
- ROI by confidence level.
- Historical model performance.

The schema is already prepared for closing line value and realized ROI tracking.

## Tests

```bash
pip install -e ".[dev]"
PYTHONPATH=python pytest
```
