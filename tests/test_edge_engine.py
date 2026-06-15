from datetime import date

from mlb_kalshi.betting.bankroll import BankrollConfig, BankrollManager
from mlb_kalshi.betting.edge_engine import EdgeEngine
from mlb_kalshi.data.schemas import Game, KalshiMarket, Prediction


def test_edge_engine_recommends_positive_ev_pick() -> None:
    game = Game(
        mlb_game_pk=1,
        game_date=date(2026, 6, 14),
        season=2026,
        home_team_abbr="NYY",
        away_team_abbr="BOS",
        starting_pitchers_confirmed=True,
    )
    prediction = Prediction(
        mlb_game_pk=1,
        prediction_date=date(2026, 6, 14),
        home_win_probability=0.58,
        away_win_probability=0.42,
        predicted_winner="home",
        confidence_score=0.16,
        confidence_rating="medium",
        feature_payload={},
        advantages={},
    )
    markets = {
        1: [
            KalshiMarket(
                market_ticker="TEST",
                event_ticker="EVENT",
                side="home",
                team_abbr="NYY",
                yes_price_cents=50,
                implied_probability=0.50,
            )
        ]
    }
    bankroll = BankrollManager(
        BankrollConfig(
            bankroll_units=100,
            fractional_kelly=0.25,
            max_bet_units=2,
            max_daily_exposure_units=8,
            fixed_unit_size=1,
            sizing_strategy="kelly",
        )
    )
    engine = EdgeEngine(bankroll, minimum_edge=0.04, minimum_confidence=0.12, require_confirmed_starters=True)
    picks = engine.find_picks([game], [prediction], markets)

    assert len(picks) == 1
    assert picks[0].recommended_team_abbr == "NYY"
    assert abs(picks[0].edge - 0.08) < 0.000001
    assert picks[0].recommended_units > 0
