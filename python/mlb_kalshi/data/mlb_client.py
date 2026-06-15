import logging
from datetime import date
from typing import Any

import requests

from mlb_kalshi.data.schemas import Game

LOGGER = logging.getLogger(__name__)

TEAM_ABBR_OVERRIDES = {
    "AZ": "ARI",
    "WSH": "WSN",
    "CWS": "CHW",
    "SF": "SFG",
    "SD": "SDP",
    "TB": "TBR",
    "KC": "KCR",
}


class MlbStatsApiClient:
    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self.base_url = "https://statsapi.mlb.com/api/v1"

    def get_schedule(self, slate_date: date) -> list[Game]:
        params = {
            "sportId": 1,
            "date": slate_date.isoformat(),
            "hydrate": "probablePitcher,team,venue,linescore",
        }
        LOGGER.info("Fetching MLB schedule for %s", slate_date)
        response = requests.get(f"{self.base_url}/schedule", params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        games: list[Game] = []
        for day in payload.get("dates", []):
            for item in day.get("games", []):
                games.append(self._parse_game(item, slate_date))
        return games

    def get_standings(self, season: int) -> dict[str, dict[str, Any]]:
        params = {"leagueId": "103,104", "season": season, "standingsTypes": "regularSeason"}
        response = requests.get(f"{self.base_url}/standings", params=params, timeout=self.timeout)
        response.raise_for_status()
        data: dict[str, dict[str, Any]] = {}
        for record in response.json().get("records", []):
            for team_record in record.get("teamRecords", []):
                abbr = self._abbr(team_record.get("team", {}).get("abbreviation", ""))
                data[abbr] = team_record
        return data

    def _parse_game(self, item: dict[str, Any], slate_date: date) -> Game:
        teams = item.get("teams", {})
        home = teams.get("home", {})
        away = teams.get("away", {})
        home_team = home.get("team", {})
        away_team = away.get("team", {})
        home_pitcher = home.get("probablePitcher") or {}
        away_pitcher = away.get("probablePitcher") or {}
        status = item.get("status", {}).get("detailedState", "scheduled")
        home_score = home.get("score")
        away_score = away.get("score")
        winning_side = None
        if isinstance(home_score, int) and isinstance(away_score, int) and status.lower() == "final":
            winning_side = "home" if home_score > away_score else "away"

        return Game(
            mlb_game_pk=int(item["gamePk"]),
            game_date=slate_date,
            season=slate_date.year,
            game_time=self._parse_datetime(item.get("gameDate")),
            home_team_abbr=self._abbr(home_team.get("abbreviation", "")),
            away_team_abbr=self._abbr(away_team.get("abbreviation", "")),
            venue=(item.get("venue") or {}).get("name"),
            status=status,
            home_score=home_score,
            away_score=away_score,
            winning_side=winning_side,
            starting_pitchers_confirmed=bool(home_pitcher and away_pitcher),
            home_probable_pitcher_id=home_pitcher.get("id"),
            away_probable_pitcher_id=away_pitcher.get("id"),
            home_probable_pitcher_name=home_pitcher.get("fullName"),
            away_probable_pitcher_name=away_pitcher.get("fullName"),
            raw_payload=item,
        )

    @staticmethod
    def _parse_datetime(value: str | None):
        if not value:
            return None
        from datetime import datetime

        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _abbr(value: str) -> str:
        value = value.upper()
        return TEAM_ABBR_OVERRIDES.get(value, value)

