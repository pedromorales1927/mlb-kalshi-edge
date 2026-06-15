#!/usr/bin/env python
import argparse
import json
from datetime import date

from mlb_kalshi.config.settings import get_settings
from mlb_kalshi.utils.logging import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MLB Kalshi daily edge pipeline")
    parser.add_argument("--date", help="Slate date in YYYY-MM-DD format")
    args = parser.parse_args()

    configure_logging()
    from mlb_kalshi.pipeline.daily import DailyPipeline, local_today

    settings = get_settings()
    slate_date = date.fromisoformat(args.date) if args.date else local_today(settings.local_timezone)
    result = DailyPipeline(settings).run(slate_date)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
