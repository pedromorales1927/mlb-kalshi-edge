create extension if not exists "pgcrypto";

create table if not exists public.teams (
  id uuid primary key default gen_random_uuid(),
  mlb_team_id integer unique,
  abbreviation text not null unique,
  name text not null,
  league text,
  division text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.games (
  id uuid primary key default gen_random_uuid(),
  mlb_game_pk bigint unique not null,
  game_date date not null,
  game_time timestamptz,
  season integer not null,
  home_team_id uuid references public.teams(id),
  away_team_id uuid references public.teams(id),
  home_team_abbr text not null,
  away_team_abbr text not null,
  venue text,
  status text not null default 'scheduled',
  home_score integer,
  away_score integer,
  winning_side text check (winning_side in ('home', 'away')),
  starting_pitchers_confirmed boolean not null default false,
  home_probable_pitcher_id bigint,
  away_probable_pitcher_id bigint,
  home_probable_pitcher_name text,
  away_probable_pitcher_name text,
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_games_game_date on public.games(game_date);
create index if not exists idx_games_teams_date on public.games(game_date, home_team_abbr, away_team_abbr);

create table if not exists public.team_daily_metrics (
  id uuid primary key default gen_random_uuid(),
  team_abbr text not null,
  metric_date date not null,
  wins integer,
  losses integer,
  win_pct numeric,
  run_differential numeric,
  runs_per_game numeric,
  runs_allowed_per_game numeric,
  home_record text,
  away_record text,
  last_10_record text,
  offensive_score numeric,
  defensive_score numeric,
  recent_form_score numeric,
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(team_abbr, metric_date)
);

create table if not exists public.pitcher_daily_metrics (
  id uuid primary key default gen_random_uuid(),
  pitcher_mlb_id bigint,
  pitcher_name text not null,
  team_abbr text,
  metric_date date not null,
  era numeric,
  whip numeric,
  fip numeric,
  xfip numeric,
  k_pct numeric,
  bb_pct numeric,
  hr_per_9 numeric,
  last_3_starts_score numeric,
  last_5_starts_score numeric,
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(pitcher_mlb_id, metric_date)
);

create table if not exists public.bullpen_daily_metrics (
  id uuid primary key default gen_random_uuid(),
  team_abbr text not null,
  metric_date date not null,
  era numeric,
  whip numeric,
  fip numeric,
  usage_last_3_days numeric,
  usage_last_7_days numeric,
  rest_advantage numeric,
  bullpen_score numeric,
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(team_abbr, metric_date)
);

create table if not exists public.kalshi_market_snapshots (
  id uuid primary key default gen_random_uuid(),
  snapshot_ts timestamptz not null default now(),
  game_id uuid references public.games(id) on delete cascade,
  market_ticker text not null,
  event_ticker text,
  side text not null check (side in ('home', 'away')),
  team_abbr text not null,
  yes_price_cents numeric not null,
  implied_probability numeric not null,
  volume numeric,
  open_interest numeric,
  raw_payload jsonb not null default '{}'::jsonb,
  unique(snapshot_ts, market_ticker, side)
);

create index if not exists idx_kalshi_game_snapshot on public.kalshi_market_snapshots(game_id, snapshot_ts desc);

create table if not exists public.model_runs (
  id uuid primary key default gen_random_uuid(),
  run_ts timestamptz not null default now(),
  model_name text not null,
  model_version text not null,
  train_start_date date,
  train_end_date date,
  test_start_date date,
  test_end_date date,
  accuracy numeric,
  roc_auc numeric,
  log_loss numeric,
  brier_score numeric,
  artifact_uri text,
  feature_version text,
  metadata jsonb not null default '{}'::jsonb
);

create table if not exists public.predictions (
  id uuid primary key default gen_random_uuid(),
  game_id uuid references public.games(id) on delete cascade,
  model_run_id uuid references public.model_runs(id),
  prediction_date date not null,
  home_win_probability numeric not null,
  away_win_probability numeric not null,
  predicted_winner text not null check (predicted_winner in ('home', 'away')),
  confidence_score numeric not null,
  confidence_rating text not null check (confidence_rating in ('low', 'medium', 'high')),
  team_strength_advantage numeric,
  starting_pitcher_advantage numeric,
  bullpen_advantage numeric,
  offensive_advantage numeric,
  situational_advantage numeric,
  recent_form_advantage numeric,
  feature_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(game_id, prediction_date, model_run_id)
);

create index if not exists idx_predictions_date on public.predictions(prediction_date);

create table if not exists public.daily_picks (
  id uuid primary key default gen_random_uuid(),
  prediction_id uuid references public.predictions(id) on delete cascade,
  game_id uuid references public.games(id) on delete cascade,
  pick_date date not null,
  recommended_side text not null check (recommended_side in ('home', 'away')),
  recommended_team_abbr text not null,
  market_ticker text,
  model_probability numeric not null,
  kalshi_probability numeric not null,
  edge numeric not null,
  expected_value numeric not null,
  confidence_score numeric not null,
  confidence_rating text not null check (confidence_rating in ('low', 'medium', 'high')),
  recommended_units numeric not null,
  recommended_risk_pct numeric not null,
  reason text not null,
  status text not null default 'open',
  created_at timestamptz not null default now(),
  unique(game_id, pick_date, recommended_side, market_ticker)
);

create index if not exists idx_daily_picks_pick_date on public.daily_picks(pick_date, edge desc);

create table if not exists public.bet_results (
  id uuid primary key default gen_random_uuid(),
  pick_id uuid references public.daily_picks(id) on delete cascade,
  game_id uuid references public.games(id) on delete cascade,
  result_date date not null,
  stake_units numeric not null,
  price_cents numeric not null,
  payout_units numeric,
  profit_units numeric,
  closing_price_cents numeric,
  clv numeric,
  outcome text check (outcome in ('win', 'loss', 'push', 'void')),
  created_at timestamptz not null default now(),
  unique(pick_id)
);

create table if not exists public.bankroll_ledger (
  id uuid primary key default gen_random_uuid(),
  ledger_date date not null,
  event_type text not null,
  amount_units numeric not null,
  bankroll_units numeric not null,
  description text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_bankroll_date on public.bankroll_ledger(ledger_date desc);

create table if not exists public.email_reports (
  id uuid primary key default gen_random_uuid(),
  report_date date not null unique,
  subject text not null,
  status text not null check (status in ('sent', 'failed', 'skipped')),
  sent_at timestamptz,
  recipient text,
  error text,
  html_report text,
  csv_report text,
  created_at timestamptz not null default now()
);

create or replace view public.dashboard_today as
select
  g.id as game_id,
  g.game_date,
  g.game_time,
  g.home_team_abbr,
  g.away_team_abbr,
  g.home_probable_pitcher_name,
  g.away_probable_pitcher_name,
  g.starting_pitchers_confirmed,
  p.home_win_probability,
  p.away_win_probability,
  p.predicted_winner,
  p.confidence_score,
  p.confidence_rating,
  dp.recommended_side,
  dp.recommended_team_abbr,
  dp.model_probability,
  dp.kalshi_probability,
  dp.edge,
  dp.expected_value,
  dp.recommended_units,
  dp.recommended_risk_pct,
  dp.reason
from public.games g
left join lateral (
  select *
  from public.predictions p
  where p.game_id = g.id
  order by p.created_at desc
  limit 1
) p on true
left join public.daily_picks dp on dp.prediction_id = p.id;

