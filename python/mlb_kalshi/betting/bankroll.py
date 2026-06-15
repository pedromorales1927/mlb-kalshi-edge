from dataclasses import dataclass


@dataclass(frozen=True)
class BankrollConfig:
    bankroll_units: float
    fractional_kelly: float
    max_bet_units: float
    max_daily_exposure_units: float
    fixed_unit_size: float
    sizing_strategy: str


class BankrollManager:
    def __init__(self, config: BankrollConfig) -> None:
        self.config = config

    def size_bets(self, opportunities: list[dict]) -> list[dict]:
        exposure = 0.0
        sized: list[dict] = []
        for opportunity in sorted(opportunities, key=lambda item: item["expected_value"], reverse=True):
            units = self._size_single(opportunity)
            available = max(self.config.max_daily_exposure_units - exposure, 0.0)
            units = min(units, available)
            if units <= 0:
                continue
            exposure += units
            sized.append(
                {
                    **opportunity,
                    "recommended_units": round(units, 3),
                    "recommended_risk_pct": round(units / self.config.bankroll_units, 4),
                }
            )
        return sized

    def _size_single(self, opportunity: dict) -> float:
        if self.config.sizing_strategy == "fixed":
            return min(self.config.fixed_unit_size, self.config.max_bet_units)

        probability = float(opportunity["model_probability"])
        price = max(float(opportunity["kalshi_probability"]), 0.01)
        decimal_odds = 1.0 / price
        b = decimal_odds - 1.0
        q = 1.0 - probability
        kelly_fraction = max((b * probability - q) / b, 0.0)
        units = self.config.bankroll_units * kelly_fraction * self.config.fractional_kelly
        return min(units, self.config.max_bet_units)

