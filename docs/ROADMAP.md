# Implementation Roadmap

## Phase 1 - Foundations

- Create Supabase schema and indexes.
- Configure environment variables for Supabase, SendGrid, Kalshi, and bankroll settings.
- Deploy the Next.js dashboard to Vercel.
- Configure GitHub Actions secrets.

## Phase 2 - Automated Daily Pipeline

- Pull MLB schedule and game metadata.
- Pull or derive team, pitcher, bullpen, and context features.
- Pull Kalshi market snapshots.
- Generate calibrated probabilities.
- Persist predictions, market snapshots, picks, and report state.
- Send daily email and failure alerts.

## Phase 3 - Modeling

- Backfill historical games.
- Train logistic regression baseline.
- Train XGBoost primary model.
- Calibrate model probabilities.
- Track accuracy, ROC AUC, log loss, and Brier score.
- Version model artifacts.

## Phase 4 - Betting Analytics

- Match Kalshi markets to MLB games.
- Calculate edge, expected value, confidence, and bet size.
- Enforce confirmed-starter, edge, confidence, and exposure thresholds.
- Track closing line value and realized ROI.

## Phase 5 - Dashboard and Operations

- Monitor top bets, full board, model performance, bankroll, and backtests.
- Add Supabase Realtime or polling refresh.
- Add failure alert routing.
- Add data-quality checks and stale-data warnings.

