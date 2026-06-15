import csv
import io
from datetime import date

from mlb_kalshi.data.schemas import Game, Pick, Prediction


class ReportRenderer:
    def render_csv(self, picks: list[Pick], predictions: list[Prediction]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "date",
                "game_pk",
                "team",
                "side",
                "model_probability",
                "kalshi_probability",
                "edge",
                "expected_value",
                "confidence",
                "units",
                "reason",
            ]
        )
        for pick in picks:
            writer.writerow(
                [
                    pick.pick_date.isoformat(),
                    pick.mlb_game_pk,
                    pick.recommended_team_abbr,
                    pick.recommended_side,
                    round(pick.model_probability, 4),
                    round(pick.kalshi_probability, 4),
                    round(pick.edge, 4),
                    round(pick.expected_value, 4),
                    pick.confidence_rating,
                    pick.recommended_units,
                    pick.reason,
                ]
            )
        return output.getvalue()

    def render_html(
        self,
        slate_date: date,
        games: list[Game],
        predictions: list[Prediction],
        picks: list[Pick],
    ) -> str:
        top = sorted(picks, key=lambda item: item.expected_value, reverse=True)[:5]
        no_bet_games = [
            game
            for game in games
            if game.mlb_game_pk not in {pick.mlb_game_pk for pick in picks}
        ]
        return f"""
<!doctype html>
<html>
<body style="margin:0;background:#f4f6f2;font-family:Arial,Helvetica,sans-serif;color:#15201a;">
  <div style="max-width:760px;margin:0 auto;padding:22px;">
    <h1 style="margin:0 0 6px;">MLB Kalshi Edge Report - {slate_date.isoformat()}</h1>
    <p style="color:#637067;margin:0 0 22px;">Expected value recommendations versus Kalshi market prices.</p>
    {self._section("Top 5 Bets Today", self._pick_table(top))}
    {self._section("All Qualifying Bets", self._pick_table(picks))}
    {self._section("No Bet Games", self._no_bet_table(no_bet_games, predictions))}
    {self._section("Model Performance Summary", "<p>See dashboard for live ROI, CLV, accuracy, and Brier score.</p>")}
    {self._section("Bankroll Recommendations", self._bankroll_summary(picks))}
  </div>
</body>
</html>
"""

    def _section(self, title: str, body: str) -> str:
        return f"""
<div style="background:#fff;border:1px solid #dce4dd;border-radius:8px;padding:16px;margin:16px 0;">
  <h2 style="margin:0 0 12px;font-size:20px;">{title}</h2>
  {body}
</div>
"""

    def _pick_table(self, picks: list[Pick]) -> str:
        if not picks:
            return "<p>No qualifying bets.</p>"
        rows = "".join(
            f"""
<tr>
  <td>{pick.recommended_team_abbr}</td>
  <td>{pick.model_probability:.1%}</td>
  <td>{pick.kalshi_probability:.1%}</td>
  <td>{pick.edge:+.1%}</td>
  <td>{pick.expected_value:+.1%}</td>
  <td>{pick.recommended_units:.2f}u</td>
  <td>{pick.confidence_rating}</td>
</tr>
"""
            for pick in picks
        )
        return f"""
<table style="width:100%;border-collapse:collapse;font-size:14px;">
  <thead><tr><th align="left">Team</th><th align="left">Model</th><th align="left">Kalshi</th><th align="left">Edge</th><th align="left">EV</th><th align="left">Units</th><th align="left">Conf.</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
"""

    def _no_bet_table(self, games: list[Game], predictions: list[Prediction]) -> str:
        predictions_by_pk = {prediction.mlb_game_pk: prediction for prediction in predictions}
        rows = "".join(
            f"<li>{game.away_team_abbr} @ {game.home_team_abbr} - {predictions_by_pk.get(game.mlb_game_pk).confidence_rating if game.mlb_game_pk in predictions_by_pk else 'no prediction'}</li>"
            for game in games
        )
        return f"<ul>{rows}</ul>" if rows else "<p>Every game with market data qualified.</p>"

    def _bankroll_summary(self, picks: list[Pick]) -> str:
        exposure = sum(pick.recommended_units for pick in picks)
        return f"<p>Total recommended exposure: <strong>{exposure:.2f} units</strong>.</p>"

