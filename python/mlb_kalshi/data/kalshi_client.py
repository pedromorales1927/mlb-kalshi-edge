import csv
import logging
from pathlib import Path
from typing import Any

import requests

from mlb_kalshi.data.schemas import Game, KalshiMarket

LOGGER = logging.getLogger(__name__)


class KalshiClient:
    def __init__(self, api_base: str, csv_path: Path | None = None, timeout: int = 30) -> None:
        self.api_base = api_base.rstrip("/")
        self.csv_path = csv_path
        self.timeout = timeout

    def get_mlb_markets(self, games: list[Game]) -> dict[int, list[KalshiMarket]]:
        if self.csv_path:
            LOGGER.info("Loading Kalshi prices from CSV %s", self.csv_path)
            return self._load_csv(self.csv_path, games)
        LOGGER.info("Fetching Kalshi MLB markets from public API")
        return self._load_api(games)

    def _load_api(self, games: list[Game]) -> dict[int, list[KalshiMarket]]:
        params = {
            "limit": 1000,
            "status": "open",
        }
        response = requests.get(f"{self.api_base}/markets", params=params, timeout=self.timeout)
        response.raise_for_status()
        markets = response.json().get("markets", [])
        matched: dict[int, list[KalshiMarket]] = {game.mlb_game_pk: [] for game in games}
        for game in games:
            for market in markets:
                text = " ".join(
                    str(market.get(key, "")) for key in ("ticker", "event_ticker", "title", "subtitle")
                )
                if not all(token.lower() in text.lower() for token in [game.home_team_abbr, game.away_team_abbr]):
                    continue
                for side, team in [("home", game.home_team_abbr), ("away", game.away_team_abbr)]:
                    if team.lower() in text.lower():
                        price = float(market.get("yes_ask") or market.get("last_price") or 0)
                        if price > 0:
                            matched[game.mlb_game_pk].append(
                                KalshiMarket(
                                    market_ticker=market.get("ticker", ""),
                                    event_ticker=market.get("event_ticker"),
                                    side=side,
                                    team_abbr=team,
                                    yes_price_cents=price,
                                    implied_probability=price / 100.0,
                                    volume=self._num(market.get("volume")),
                                    open_interest=self._num(market.get("open_interest")),
                                    raw_payload=market,
                                )
                            )
        return matched

    def _load_csv(self, path: Path, games: list[Game]) -> dict[int, list[KalshiMarket]]:
        game_by_pair = {
            (game.away_team_abbr, game.home_team_abbr): game.mlb_game_pk for game in games
        }
        out: dict[int, list[KalshiMarket]] = {game.mlb_game_pk: [] for game in games}
        with path.open("r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                away = row.get("away_team") or row.get("away_team_abbr")
                home = row.get("home_team") or row.get("home_team_abbr")
                side = (row.get("side") or "").lower()
                price = float(row.get("yes_price_cents") or row.get("price") or 0)
                if not away or not home or side not in {"home", "away"} or price <= 0:
                    continue
                game_pk = game_by_pair.get((away.upper(), home.upper()))
                if not game_pk:
                    continue
                team = home.upper() if side == "home" else away.upper()
                out[game_pk].append(
                    KalshiMarket(
                        market_ticker=row.get("market_ticker") or row.get("ticker") or "",
                        event_ticker=row.get("event_ticker"),
                        side=side,
                        team_abbr=team,
                        yes_price_cents=price,
                        implied_probability=price / 100.0,
                        volume=self._num(row.get("volume")),
                        open_interest=self._num(row.get("open_interest")),
                        raw_payload=dict(row),
                    )
                )
        return out

    @staticmethod
    def _num(value: Any) -> float | None:
        try:
            return None if value in (None, "") else float(value)
        except (TypeError, ValueError):
            return None
