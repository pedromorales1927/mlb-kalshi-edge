from datetime import date
from typing import Any

import pandas as pd

from mlb_kalshi.data.schemas import Game


class FeatureBuilder:
    def build_daily_features(
        self,
        games: list[Game],
        standings: dict[str, dict[str, Any]],
        slate_date: date,
    ) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        for game in games:
            home = standings.get(game.home_team_abbr, {})
            away = standings.get(game.away_team_abbr, {})
            home_wpct = self._pct(home)
            away_wpct = self._pct(away)
            home_rd = self._run_diff(home)
            away_rd = self._run_diff(away)
            team_strength_advantage = (home_wpct - away_wpct) + 0.002 * (home_rd - away_rd)
            starting_pitcher_advantage = 0.0
            bullpen_advantage = 0.0
            offensive_advantage = self._runs_per_game(home) - self._runs_per_game(away)
            situational_advantage = 0.035
            recent_form_advantage = self._last_ten_pct(home) - self._last_ten_pct(away)
            rows.append(
                {
                    "mlb_game_pk": game.mlb_game_pk,
                    "prediction_date": slate_date,
                    "home_team_abbr": game.home_team_abbr,
                    "away_team_abbr": game.away_team_abbr,
                    "starting_pitchers_confirmed": game.starting_pitchers_confirmed,
                    "team_strength_advantage": team_strength_advantage,
                    "starting_pitcher_advantage": starting_pitcher_advantage,
                    "bullpen_advantage": bullpen_advantage,
                    "offensive_advantage": offensive_advantage,
                    "situational_advantage": situational_advantage,
                    "recent_form_advantage": recent_form_advantage,
                    "home_win_pct": home_wpct,
                    "away_win_pct": away_wpct,
                    "home_run_diff": home_rd,
                    "away_run_diff": away_rd,
                }
            )
        return pd.DataFrame(rows)

    @staticmethod
    def feature_columns() -> list[str]:
        return [
            "team_strength_advantage",
            "starting_pitcher_advantage",
            "bullpen_advantage",
            "offensive_advantage",
            "situational_advantage",
            "recent_form_advantage",
            "home_win_pct",
            "away_win_pct",
            "home_run_diff",
            "away_run_diff",
        ]

    @staticmethod
    def _pct(record: dict[str, Any]) -> float:
        try:
            return float(record.get("winningPercentage", "0.500"))
        except (TypeError, ValueError):
            wins = float(record.get("wins", 0))
            losses = float(record.get("losses", 0))
            return wins / max(wins + losses, 1.0)

    @staticmethod
    def _run_diff(record: dict[str, Any]) -> float:
        return float(record.get("runDifferential") or 0)

    @staticmethod
    def _runs_per_game(record: dict[str, Any]) -> float:
        runs = float(record.get("runsScored") or 0)
        games = float(record.get("gamesPlayed") or max(float(record.get("wins", 0)) + float(record.get("losses", 0)), 1))
        return runs / max(games, 1.0)

    @staticmethod
    def _last_ten_pct(record: dict[str, Any]) -> float:
        split = record.get("records", {}).get("splitRecords", []) if record else []
        for item in split:
            if item.get("type") == "lastTen":
                wins = float(item.get("wins", 0))
                losses = float(item.get("losses", 0))
                return wins / max(wins + losses, 1.0)
        return 0.5

