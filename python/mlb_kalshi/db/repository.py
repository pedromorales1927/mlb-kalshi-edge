import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import math

from supabase import Client, create_client

from mlb_kalshi.data.schemas import Game, KalshiMarket, Pick, Prediction

LOGGER = logging.getLogger(__name__)


def to_json_safe(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, float):
        return None if math.isnan(value) or math.isinf(value) else value
    if isinstance(value, dict):
        return {str(key): to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return to_json_safe(value.item())
        except (TypeError, ValueError):
            pass
    return value


class SupabaseRepository:
    def __init__(self, supabase_url: str, service_role_key: str) -> None:
        self.client: Client = create_client(supabase_url, service_role_key)

    def upsert_games(self, games: list[Game]) -> dict[int, str]:
        rows = [
            {
                "mlb_game_pk": game.mlb_game_pk,
                "game_date": game.game_date.isoformat(),
                "game_time": game.game_time.isoformat() if game.game_time else None,
                "season": game.season,
                "home_team_abbr": game.home_team_abbr,
                "away_team_abbr": game.away_team_abbr,
                "venue": game.venue,
                "status": game.status,
                "home_score": game.home_score,
                "away_score": game.away_score,
                "winning_side": game.winning_side,
                "starting_pitchers_confirmed": game.starting_pitchers_confirmed,
                "home_probable_pitcher_id": game.home_probable_pitcher_id,
                "away_probable_pitcher_id": game.away_probable_pitcher_id,
                "home_probable_pitcher_name": game.home_probable_pitcher_name,
                "away_probable_pitcher_name": game.away_probable_pitcher_name,
                "raw_payload": to_json_safe(game.raw_payload),
            }
            for game in games
        ]
        if rows:
            self.client.table("games").upsert(rows, on_conflict="mlb_game_pk").execute()
        response = (
            self.client.table("games")
            .select("id, mlb_game_pk")
            .in_("mlb_game_pk", [game.mlb_game_pk for game in games])
            .execute()
        )
        return {int(row["mlb_game_pk"]): row["id"] for row in response.data or []}

    def create_model_run(self, metrics: dict[str, Any] | None = None) -> str:
        payload = {
            "model_name": "xgboost_calibrated",
            "model_version": "daily",
            "feature_version": "v1",
            "metadata": metrics or {},
            "accuracy": (metrics or {}).get("accuracy"),
            "roc_auc": (metrics or {}).get("roc_auc"),
            "log_loss": (metrics or {}).get("log_loss"),
            "brier_score": (metrics or {}).get("brier_score"),
        }
        response = self.client.table("model_runs").insert(payload).execute()
        return response.data[0]["id"]

    def upsert_daily_metrics(
        self,
        team_metrics: list[dict[str, Any]],
        pitcher_metrics: list[dict[str, Any]],
        bullpen_metrics: list[dict[str, Any]],
    ) -> None:
        if team_metrics:
            self.client.table("team_daily_metrics").upsert(
                team_metrics, on_conflict="team_abbr,metric_date"
            ).execute()
        if pitcher_metrics:
            self.client.table("pitcher_daily_metrics").upsert(
                pitcher_metrics, on_conflict="pitcher_mlb_id,metric_date"
            ).execute()
        if bullpen_metrics:
            self.client.table("bullpen_daily_metrics").upsert(
                bullpen_metrics, on_conflict="team_abbr,metric_date"
            ).execute()

    def insert_market_snapshots(
        self, game_id_by_pk: dict[int, str], markets_by_game: dict[int, list[KalshiMarket]]
    ) -> None:
        rows: list[dict[str, Any]] = []
        for game_pk, markets in markets_by_game.items():
            for market in markets:
                rows.append(
                    {
                        "game_id": game_id_by_pk.get(game_pk),
                        "market_ticker": market.market_ticker,
                        "event_ticker": market.event_ticker,
                        "side": market.side,
                        "team_abbr": market.team_abbr,
                        "yes_price_cents": market.yes_price_cents,
                        "implied_probability": market.implied_probability,
                        "volume": market.volume,
                        "open_interest": market.open_interest,
                        "raw_payload": to_json_safe(market.raw_payload),
                    }
                )
        if rows:
            self.client.table("kalshi_market_snapshots").insert(rows).execute()

    def insert_predictions(
        self,
        game_id_by_pk: dict[int, str],
        model_run_id: str,
        predictions: list[Prediction],
    ) -> dict[int, str]:
        rows = [
            {
                "game_id": game_id_by_pk[prediction.mlb_game_pk],
                "model_run_id": model_run_id,
                "prediction_date": prediction.prediction_date.isoformat(),
                "home_win_probability": prediction.home_win_probability,
                "away_win_probability": prediction.away_win_probability,
                "predicted_winner": prediction.predicted_winner,
                "confidence_score": prediction.confidence_score,
                "confidence_rating": prediction.confidence_rating,
                **prediction.advantages,
                "feature_payload": to_json_safe(prediction.feature_payload),
            }
            for prediction in predictions
        ]
        if rows:
            self.client.table("predictions").upsert(
                rows, on_conflict="game_id,prediction_date,model_run_id"
            ).execute()
        response = (
            self.client.table("predictions")
            .select("id, game_id, games(mlb_game_pk)")
            .eq("model_run_id", model_run_id)
            .execute()
        )
        out: dict[int, str] = {}
        for row in response.data or []:
            games = row.get("games") or {}
            out[int(games["mlb_game_pk"])] = row["id"]
        return out

    def upsert_picks(
        self,
        game_id_by_pk: dict[int, str],
        prediction_id_by_pk: dict[int, str],
        picks: list[Pick],
    ) -> None:
        rows = [
            {
                "prediction_id": prediction_id_by_pk[pick.mlb_game_pk],
                "game_id": game_id_by_pk[pick.mlb_game_pk],
                "pick_date": pick.pick_date.isoformat(),
                "recommended_side": pick.recommended_side,
                "recommended_team_abbr": pick.recommended_team_abbr,
                "market_ticker": pick.market_ticker,
                "model_probability": pick.model_probability,
                "kalshi_probability": pick.kalshi_probability,
                "edge": pick.edge,
                "expected_value": pick.expected_value,
                "confidence_score": pick.confidence_score,
                "confidence_rating": pick.confidence_rating,
                "recommended_units": pick.recommended_units,
                "recommended_risk_pct": pick.recommended_risk_pct,
                "reason": pick.reason,
            }
            for pick in picks
        ]
        if rows:
            self.client.table("daily_picks").upsert(
                rows, on_conflict="game_id,pick_date,recommended_side,market_ticker"
            ).execute()

    def get_latest_bankroll(self, default_units: float) -> float:
        response = (
            self.client.table("bankroll_ledger")
            .select("bankroll_units")
            .order("ledger_date", desc=True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return float(response.data[0]["bankroll_units"])
        return default_units

    def record_email_report(
        self,
        report_date: date,
        subject: str,
        status: str,
        recipient: str | None,
        html_report: str | None,
        csv_report: str | None,
        error: str | None = None,
    ) -> None:
        self.client.table("email_reports").upsert(
            {
                "report_date": report_date.isoformat(),
                "subject": subject,
                "status": status,
                "sent_at": datetime.now(timezone.utc).isoformat() if status == "sent" else None,
                "recipient": recipient,
                "error": error,
                "html_report": html_report,
                "csv_report": csv_report,
            },
            on_conflict="report_date",
        ).execute()
