#!/usr/bin/env python
import argparse
import json

import pandas as pd

from mlb_kalshi.features.builder import FeatureBuilder
from mlb_kalshi.models.training import ModelTrainer
from mlb_kalshi.utils.logging import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Train calibrated MLB win probability model")
    parser.add_argument("--input", required=True, help="Historical feature dataset CSV")
    parser.add_argument("--output", default="artifacts/model.joblib", help="Model artifact path")
    parser.add_argument("--model", default="xgboost", choices=["xgboost", "logistic"])
    args = parser.parse_args()

    configure_logging()
    dataset = pd.read_csv(args.input, parse_dates=["game_date"])
    trainer = ModelTrainer()
    model, metrics = trainer.train(dataset, FeatureBuilder.feature_columns(), model_name=args.model)
    trainer.save(model, args.output, {"model": args.model, **metrics.__dict__})
    print(json.dumps(metrics.__dict__, indent=2))


if __name__ == "__main__":
    main()

