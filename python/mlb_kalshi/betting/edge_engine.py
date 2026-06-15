from datetime import date
from typing import TYPE_CHECKING

from mlb_kalshi.betting.bankroll import BankrollManager
from mlb_kalshi.data.schemas import Game, KalshiMarket, Pick, Prediction

if TYPE_CHECKING:
    import pandas as pd


class EdgeEngine:
    def __init__(
        self,
        bankroll_manager: BankrollManager,
        minimum_edge: float,
        minimum_confidence: float,
        require_confirmed_starters: bool,
    ) -> None:
        self.bankroll_manager = bankroll_manager
        self.minimum_edge = minimum_edge
        self.minimum_confidence = minimum_confidence
        self.require_confirmed_starters = require_confirmed_starters

    def predictions_from_probabilities(
        self,
        games: list[Game],
        feature_frame: "pd.DataFrame",
        home_probabilities: list[float],
        slate_date: date,
    ) -> list[Prediction]:
        feature_by_game = feature_frame.set_index("mlb_game_pk").to_dict(orient="index")
        predictions: list[Prediction] = []
        for game, home_probability in zip(games, home_probabilities, strict=True):
            home_probability = min(max(float(home_probability), 0.01), 0.99)
            away_probability = 1.0 - home_probability
            confidence_score = abs(home_probability - 0.5) * 2
            rating = "high" if confidence_score >= 0.22 else "medium" if confidence_score >= 0.12 else "low"
            features = feature_by_game[game.mlb_game_pk]
            predictions.append(
                Prediction(
                    mlb_game_pk=game.mlb_game_pk,
                    prediction_date=slate_date,
                    home_win_probability=home_probability,
                    away_win_probability=away_probability,
                    predicted_winner="home" if home_probability >= away_probability else "away",
                    confidence_score=confidence_score,
                    confidence_rating=rating,
                    feature_payload=features,
                    advantages={
                        "team_strength_advantage": float(features.get("team_strength_advantage", 0)),
                        "starting_pitcher_advantage": float(features.get("starting_pitcher_advantage", 0)),
                        "bullpen_advantage": float(features.get("bullpen_advantage", 0)),
                        "offensive_advantage": float(features.get("offensive_advantage", 0)),
                        "situational_advantage": float(features.get("situational_advantage", 0)),
                        "recent_form_advantage": float(features.get("recent_form_advantage", 0)),
                    },
                )
            )
        return predictions

    def find_picks(
        self,
        games: list[Game],
        predictions: list[Prediction],
        markets_by_game: dict[int, list[KalshiMarket]],
    ) -> list[Pick]:
        games_by_pk = {game.mlb_game_pk: game for game in games}
        predictions_by_pk = {prediction.mlb_game_pk: prediction for prediction in predictions}
        raw_opportunities: list[dict] = []

        for game_pk, markets in markets_by_game.items():
            game = games_by_pk[game_pk]
            prediction = predictions_by_pk[game_pk]
            if self.require_confirmed_starters and not game.starting_pitchers_confirmed:
                continue
            if prediction.confidence_score < self.minimum_confidence:
                continue
            for market in markets:
                model_probability = (
                    prediction.home_win_probability
                    if market.side == "home"
                    else prediction.away_win_probability
                )
                edge = model_probability - market.implied_probability
                if edge < self.minimum_edge:
                    continue
                expected_value = self._expected_value(model_probability, market.implied_probability)
                raw_opportunities.append(
                    {
                        "mlb_game_pk": game_pk,
                        "pick_date": prediction.prediction_date,
                        "recommended_side": market.side,
                        "recommended_team_abbr": market.team_abbr,
                        "market_ticker": market.market_ticker,
                        "model_probability": model_probability,
                        "kalshi_probability": market.implied_probability,
                        "edge": edge,
                        "expected_value": expected_value,
                        "confidence_score": prediction.confidence_score,
                        "confidence_rating": prediction.confidence_rating,
                        "reason": self._reason(game, prediction, market, edge),
                    }
                )

        sized = self.bankroll_manager.size_bets(raw_opportunities)
        return [Pick(**item) for item in sized]

    @staticmethod
    def _expected_value(model_probability: float, market_probability: float) -> float:
        price = max(market_probability, 0.01)
        profit_if_win = (1.0 - price) / price
        return model_probability * profit_if_win - (1.0 - model_probability)

    @staticmethod
    def _reason(game: Game, prediction: Prediction, market: KalshiMarket, edge: float) -> str:
        winner = game.home_team_abbr if prediction.predicted_winner == "home" else game.away_team_abbr
        return (
            f"Model prices {market.team_abbr} above market by {edge * 100:.1f}%. "
            f"Projected winner: {winner}; confidence {prediction.confidence_rating}."
        )
