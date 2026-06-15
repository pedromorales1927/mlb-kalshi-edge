from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class Game:
    mlb_game_pk: int
    game_date: date
    season: int
    home_team_abbr: str
    away_team_abbr: str
    game_time: datetime | None = None
    venue: str | None = None
    status: str = "scheduled"
    home_score: int | None = None
    away_score: int | None = None
    winning_side: str | None = None
    starting_pitchers_confirmed: bool = False
    home_probable_pitcher_id: int | None = None
    away_probable_pitcher_id: int | None = None
    home_probable_pitcher_name: str | None = None
    away_probable_pitcher_name: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KalshiMarket:
    market_ticker: str
    event_ticker: str | None
    side: str
    team_abbr: str
    yes_price_cents: float
    implied_probability: float
    volume: float | None = None
    open_interest: float | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Prediction:
    mlb_game_pk: int
    prediction_date: date
    home_win_probability: float
    away_win_probability: float
    predicted_winner: str
    confidence_score: float
    confidence_rating: str
    feature_payload: dict[str, Any]
    advantages: dict[str, float]


@dataclass(frozen=True)
class Pick:
    mlb_game_pk: int
    pick_date: date
    recommended_side: str
    recommended_team_abbr: str
    market_ticker: str | None
    model_probability: float
    kalshi_probability: float
    edge: float
    expected_value: float
    confidence_score: float
    confidence_rating: str
    recommended_units: float
    recommended_risk_pct: float
    reason: str

