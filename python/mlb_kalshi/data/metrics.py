from datetime import date
from typing import Any

from mlb_kalshi.data.schemas import Game


class DailyMetricsBuilder:
    def build_team_metrics(
        self, standings: dict[str, dict[str, Any]], metric_date: date
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for team_abbr, record in standings.items():
            wins = int(record.get("wins") or 0)
            losses = int(record.get("losses") or 0)
            games = max(wins + losses, 1)
            runs_scored = float(record.get("runsScored") or 0)
            runs_allowed = float(record.get("runsAllowed") or 0)
            run_differential = float(record.get("runDifferential") or runs_scored - runs_allowed)
            rows.append(
                {
                    "team_abbr": team_abbr,
                    "metric_date": metric_date.isoformat(),
                    "wins": wins,
                    "losses": losses,
                    "win_pct": wins / games,
                    "run_differential": run_differential,
                    "runs_per_game": runs_scored / games,
                    "runs_allowed_per_game": runs_allowed / games,
                    "home_record": self._split_record(record, "home"),
                    "away_record": self._split_record(record, "away"),
                    "last_10_record": self._split_record(record, "lastTen"),
                    "offensive_score": runs_scored / games,
                    "defensive_score": -runs_allowed / games,
                    "recent_form_score": self._last_ten_pct(record),
                    "raw_payload": record,
                }
            )
        return rows

    def build_pitcher_metrics(self, games: list[Game], metric_date: date) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for game in games:
            for pitcher_id, pitcher_name, team in [
                (game.home_probable_pitcher_id, game.home_probable_pitcher_name, game.home_team_abbr),
                (game.away_probable_pitcher_id, game.away_probable_pitcher_name, game.away_team_abbr),
            ]:
                if not pitcher_id or not pitcher_name:
                    continue
                rows.append(
                    {
                        "pitcher_mlb_id": pitcher_id,
                        "pitcher_name": pitcher_name,
                        "team_abbr": team,
                        "metric_date": metric_date.isoformat(),
                        "raw_payload": {"source": "mlb_probable_pitcher"},
                    }
                )
        return rows

    def build_bullpen_metrics(
        self, standings: dict[str, dict[str, Any]], metric_date: date
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for team_abbr, record in standings.items():
            rows.append(
                {
                    "team_abbr": team_abbr,
                    "metric_date": metric_date.isoformat(),
                    "bullpen_score": 0.0,
                    "rest_advantage": 0.0,
                    "raw_payload": {"source": "placeholder_until_statcast_bullpen_backfill", "team": record.get("team")},
                }
            )
        return rows

    @staticmethod
    def _split_record(record: dict[str, Any], split_type: str) -> str | None:
        for item in record.get("records", {}).get("splitRecords", []):
            if item.get("type") == split_type:
                return f"{item.get('wins', 0)}-{item.get('losses', 0)}"
        return None

    @staticmethod
    def _last_ten_pct(record: dict[str, Any]) -> float:
        for item in record.get("records", {}).get("splitRecords", []):
            if item.get("type") == "lastTen":
                wins = float(item.get("wins", 0))
                losses = float(item.get("losses", 0))
                return wins / max(wins + losses, 1.0)
        return 0.5

