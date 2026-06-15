import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import joblib
import numpy as np

if TYPE_CHECKING:
    import pandas as pd

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelMetrics:
    accuracy: float
    roc_auc: float
    log_loss: float
    brier_score: float


class ModelTrainer:
    def train(
        self,
        dataset: "pd.DataFrame",
        feature_columns: list[str],
        target_column: str = "home_win",
        model_name: str = "xgboost",
    ) -> tuple[Any, ModelMetrics]:
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
        from sklearn.model_selection import TimeSeriesSplit

        dataset = dataset.sort_values("game_date")
        split_idx = int(len(dataset) * 0.8)
        train_df = dataset.iloc[:split_idx]
        test_df = dataset.iloc[split_idx:]
        x_train = train_df[feature_columns]
        y_train = train_df[target_column]
        x_test = test_df[feature_columns]
        y_test = test_df[target_column]

        base_model = self._build_model(model_name)
        calibrated = CalibratedClassifierCV(base_model, method="isotonic", cv=TimeSeriesSplit(n_splits=3))
        calibrated.fit(x_train, y_train)
        probabilities = calibrated.predict_proba(x_test)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
        metrics = ModelMetrics(
            accuracy=float(accuracy_score(y_test, predictions)),
            roc_auc=float(roc_auc_score(y_test, probabilities)),
            log_loss=float(log_loss(y_test, probabilities)),
            brier_score=float(brier_score_loss(y_test, probabilities)),
        )
        return calibrated, metrics

    def save(self, model: Any, path: Path, metadata: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": model, "metadata": metadata}, path)
        LOGGER.info("Saved model artifact to %s", path)

    def _build_model(self, model_name: str) -> Any:
        if model_name == "xgboost":
            try:
                from xgboost import XGBClassifier

                return XGBClassifier(
                    n_estimators=350,
                    learning_rate=0.03,
                    max_depth=3,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    eval_metric="logloss",
                    random_state=42,
                )
            except ImportError:
                LOGGER.warning("xgboost not installed; falling back to logistic regression")

        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        return Pipeline(
            steps=[
                ("scale", StandardScaler()),
                ("model", LogisticRegression(max_iter=2000, C=0.75)),
            ]
        )


class PredictionModel:
    def __init__(self, artifact_path: Path, feature_columns: list[str]) -> None:
        self.artifact_path = artifact_path
        self.feature_columns = feature_columns
        self.model: Any | None = None
        self.metadata: dict[str, Any] = {}
        if artifact_path.exists():
            payload = joblib.load(artifact_path)
            self.model = payload["model"]
            self.metadata = payload.get("metadata", {})

    def predict_home_probabilities(self, features: "pd.DataFrame") -> np.ndarray:
        x = features[self.feature_columns].fillna(0.0)
        if self.model is None:
            LOGGER.warning("No model artifact found. Using transparent baseline probability formula.")
            signal = (
                1.4 * x["team_strength_advantage"]
                + 0.35 * x["starting_pitcher_advantage"]
                + 0.25 * x["bullpen_advantage"]
                + 0.12 * x["offensive_advantage"]
                + 0.8 * x["situational_advantage"]
                + 0.4 * x["recent_form_advantage"]
            )
            return 1.0 / (1.0 + np.exp(-signal))
        return self.model.predict_proba(x)[:, 1]
