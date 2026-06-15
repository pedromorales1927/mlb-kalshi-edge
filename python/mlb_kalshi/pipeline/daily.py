import logging
from datetime import date
from zoneinfo import ZoneInfo

from mlb_kalshi.betting.bankroll import BankrollConfig, BankrollManager
from mlb_kalshi.betting.edge_engine import EdgeEngine
from mlb_kalshi.config.settings import Settings
from mlb_kalshi.data.kalshi_client import KalshiClient
from mlb_kalshi.data.metrics import DailyMetricsBuilder
from mlb_kalshi.data.mlb_client import MlbStatsApiClient
from mlb_kalshi.db.repository import SupabaseRepository
from mlb_kalshi.features.builder import FeatureBuilder
from mlb_kalshi.models.training import PredictionModel
from mlb_kalshi.reporting.emailer import SendGridEmailer
from mlb_kalshi.reporting.report import ReportRenderer

LOGGER = logging.getLogger(__name__)


class DailyPipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.mlb = MlbStatsApiClient()
        self.kalshi = KalshiClient(settings.kalshi_api_base, settings.kalshi_csv_path)
        self.repository = SupabaseRepository(
            str(settings.supabase_url), settings.supabase_service_role_key
        )
        self.feature_builder = FeatureBuilder()
        self.metrics_builder = DailyMetricsBuilder()
        self.report_renderer = ReportRenderer()
        self.emailer = SendGridEmailer(
            settings.sendgrid_api_key,
            settings.report_email_from,
            settings.report_email_to,
        )

    def run(self, slate_date: date | None = None) -> dict[str, int]:
        slate_date = slate_date or date.today()
        failed_step = "startup"
        try:
            failed_step = "fetch_mlb_schedule"
            games = self.mlb.get_schedule(slate_date)
            LOGGER.info("Fetched %d MLB games", len(games))

            failed_step = "fetch_team_stats"
            standings = self.mlb.get_standings(slate_date.year)
            team_metrics = self.metrics_builder.build_team_metrics(standings, slate_date)
            pitcher_metrics = self.metrics_builder.build_pitcher_metrics(games, slate_date)
            bullpen_metrics = self.metrics_builder.build_bullpen_metrics(standings, slate_date)

            failed_step = "build_features"
            feature_frame = self.feature_builder.build_daily_features(games, standings, slate_date)

            failed_step = "fetch_kalshi_prices"
            markets_by_game = self.kalshi.get_mlb_markets(games)

            failed_step = "generate_predictions"
            model = PredictionModel(
                self.settings.model_artifact_path,
                self.feature_builder.feature_columns(),
            )
            probabilities = model.predict_home_probabilities(feature_frame).tolist()

            bankroll_units = self.repository.get_latest_bankroll(
                self.settings.default_bankroll_units
            )
            bankroll = BankrollManager(
                BankrollConfig(
                    bankroll_units=bankroll_units,
                    fractional_kelly=self.settings.fractional_kelly,
                    max_bet_units=self.settings.max_bet_units,
                    max_daily_exposure_units=self.settings.max_daily_exposure_units,
                    fixed_unit_size=self.settings.fixed_unit_size,
                    sizing_strategy=self.settings.sizing_strategy,
                )
            )
            edge_engine = EdgeEngine(
                bankroll,
                self.settings.minimum_edge,
                self.settings.minimum_confidence,
                self.settings.require_confirmed_starters,
            )
            predictions = edge_engine.predictions_from_probabilities(
                games, feature_frame, probabilities, slate_date
            )
            picks = edge_engine.find_picks(games, predictions, markets_by_game)
            LOGGER.info("Generated %d predictions and %d picks", len(predictions), len(picks))

            failed_step = "database_update"
            game_id_by_pk = self.repository.upsert_games(games)
            self.repository.upsert_daily_metrics(team_metrics, pitcher_metrics, bullpen_metrics)
            model_run_id = self.repository.create_model_run(model.metadata)
            self.repository.insert_market_snapshots(game_id_by_pk, markets_by_game)
            prediction_id_by_pk = self.repository.insert_predictions(
                game_id_by_pk, model_run_id, predictions
            )
            self.repository.upsert_picks(game_id_by_pk, prediction_id_by_pk, picks)

            failed_step = "report_generation"
            html = self.report_renderer.render_html(slate_date, games, predictions, picks)
            csv_text = self.report_renderer.render_csv(picks, predictions)
            subject = f"MLB Kalshi Edge Report - {slate_date.isoformat()}"

            failed_step = "send_email"
            sent = self.emailer.send_report(subject, html, csv_text)
            self.repository.record_email_report(
                slate_date,
                subject,
                "sent" if sent else "skipped",
                self.settings.report_email_to,
                html,
                csv_text,
            )
            return {
                "games": len(games),
                "markets": sum(len(markets) for markets in markets_by_game.values()),
                "predictions": len(predictions),
                "picks": len(picks),
            }
        except Exception as error:
            LOGGER.exception("Daily pipeline failed at %s", failed_step)
            self.emailer.send_error(self.settings.alert_email_to, failed_step, error)
            raise


def local_today(timezone_name: str) -> date:
    from datetime import datetime

    return datetime.now(ZoneInfo(timezone_name)).date()
