from mlb_kalshi.betting.bankroll import BankrollConfig, BankrollManager


def test_daily_exposure_cap_is_enforced() -> None:
    manager = BankrollManager(
        BankrollConfig(
            bankroll_units=100,
            fractional_kelly=1,
            max_bet_units=10,
            max_daily_exposure_units=3,
            fixed_unit_size=1,
            sizing_strategy="kelly",
        )
    )
    opportunities = [
        {"model_probability": 0.7, "kalshi_probability": 0.5, "expected_value": 0.4},
        {"model_probability": 0.7, "kalshi_probability": 0.5, "expected_value": 0.3},
    ]
    sized = manager.size_bets(opportunities)

    assert sum(item["recommended_units"] for item in sized) <= 3

