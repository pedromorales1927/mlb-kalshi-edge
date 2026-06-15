import { format, subDays } from "date-fns";
import type { DashboardData, PerformancePoint } from "./types";
import { createServiceClient } from "./supabase";

type DashboardRow = {
  game_id: string;
  game_date: string;
  game_time: string | null;
  home_team_abbr: string;
  away_team_abbr: string;
  home_probable_pitcher_name: string | null;
  away_probable_pitcher_name: string | null;
  starting_pitchers_confirmed: boolean;
  home_win_probability: number | null;
  away_win_probability: number | null;
  predicted_winner: "home" | "away" | null;
  confidence_rating: "low" | "medium" | "high" | null;
  confidence_score: number | null;
  recommended_side: "home" | "away" | null;
  recommended_team_abbr: string | null;
  model_probability: number | null;
  kalshi_probability: number | null;
  edge: number | null;
  expected_value: number | null;
  recommended_units: number | null;
  reason: string | null;
};

function pct(value: number | null | undefined): number {
  return Number(value ?? 0);
}

function emptyPoints(labels: string[]): PerformancePoint[] {
  return labels.map((label) => ({ label, roi: 0, profit: 0, brier: 0 }));
}

export async function getDashboardData(date = new Date()): Promise<DashboardData> {
  const supabase = createServiceClient();
  const slateDate = format(date, "yyyy-MM-dd");

  const [todayRows, resultsRows, bankrollRows, modelRows] = await Promise.all([
    supabase
      .from("dashboard_today")
      .select("*")
      .eq("game_date", slateDate)
      .order("edge", { ascending: false, nullsFirst: false }),
    supabase
      .from("bet_results")
      .select("result_date, profit_units, stake_units, clv, outcome")
      .gte("result_date", format(subDays(date, 365), "yyyy-MM-dd")),
    supabase
      .from("bankroll_ledger")
      .select("ledger_date, amount_units, bankroll_units")
      .gte("ledger_date", format(subDays(date, 31), "yyyy-MM-dd"))
      .order("ledger_date", { ascending: true }),
    supabase
      .from("model_runs")
      .select("run_ts, accuracy, brier_score")
      .order("run_ts", { ascending: false })
      .limit(20)
  ]);

  if (todayRows.error) throw todayRows.error;
  if (resultsRows.error) throw resultsRows.error;
  if (bankrollRows.error) throw bankrollRows.error;
  if (modelRows.error) throw modelRows.error;

  const rows = (todayRows.data ?? []) as DashboardRow[];
  const picks = rows.filter((row) => row.recommended_team_abbr && row.edge !== null);
  const topBets = picks.slice(0, 5).map((row, index) => ({
    id: `${row.game_id}-${row.recommended_side ?? "pick"}`,
    rank: index + 1,
    game: `${row.away_team_abbr} @ ${row.home_team_abbr}`,
    gameTime: row.game_time,
    recommendedSide: row.recommended_side ?? "home",
    recommendedTeam: row.recommended_team_abbr ?? row.home_team_abbr,
    modelProbability: pct(row.model_probability),
    kalshiProbability: pct(row.kalshi_probability),
    edge: pct(row.edge),
    expectedValue: pct(row.expected_value),
    recommendedUnits: pct(row.recommended_units),
    confidenceRating: row.confidence_rating ?? "low",
    confidenceScore: pct(row.confidence_score),
    reason: row.reason ?? "No model rationale available."
  }));

  const board = rows.map((row) => {
    const winProbability =
      row.predicted_winner === "home" ? row.home_win_probability : row.away_win_probability;
    return {
      gameId: row.game_id,
      gameDate: row.game_date,
      gameTime: row.game_time,
      homeTeam: row.home_team_abbr,
      awayTeam: row.away_team_abbr,
      homePitcher: row.home_probable_pitcher_name,
      awayPitcher: row.away_probable_pitcher_name,
      startersConfirmed: row.starting_pitchers_confirmed,
      predictedWinner: row.predicted_winner,
      winProbability,
      edge: row.edge,
      confidenceRating: row.confidence_rating
    };
  });

  const results = resultsRows.data ?? [];
  const totalProfit = results.reduce((sum, row) => sum + Number(row.profit_units ?? 0), 0);
  const totalStake = results.reduce((sum, row) => sum + Math.abs(Number(row.stake_units ?? 0)), 0);
  const wins = results.filter((row) => row.outcome === "win").length;
  const settled = results.filter((row) => row.outcome === "win" || row.outcome === "loss").length;
  const avgClv =
    results.length > 0
      ? results.reduce((sum, row) => sum + Number(row.clv ?? 0), 0) / results.length
      : 0;
  const latestBankroll = bankrollRows.data?.at(-1);
  const dailyProfit = (bankrollRows.data ?? [])
    .filter((row) => row.ledger_date === slateDate)
    .reduce((sum, row) => sum + Number(row.amount_units ?? 0), 0);
  const weeklyProfit = (bankrollRows.data ?? [])
    .filter((row) => row.ledger_date >= format(subDays(date, 7), "yyyy-MM-dd"))
    .reduce((sum, row) => sum + Number(row.amount_units ?? 0), 0);
  const monthlyProfit = (bankrollRows.data ?? []).reduce(
    (sum, row) => sum + Number(row.amount_units ?? 0),
    0
  );
  const latestModel = modelRows.data?.[0];

  return {
    generatedAt: new Date().toISOString(),
    slateDate,
    topBets,
    board,
    performance: {
      historicalRoi: totalStake > 0 ? totalProfit / totalStake : 0,
      winRate: settled > 0 ? wins / settled : 0,
      clv: avgClv,
      totalProfit,
      accuracy: Number(latestModel?.accuracy ?? 0),
      brierScore: Number(latestModel?.brier_score ?? 0),
      points: emptyPoints(["30D", "60D", "90D", "180D", "365D"]).map((point, index) => ({
        ...point,
        profit: totalProfit * ((index + 1) / 5),
        roi: totalStake > 0 ? (totalProfit / totalStake) * ((index + 1) / 5) : 0,
        brier: Number(latestModel?.brier_score ?? 0)
      }))
    },
    bankroll: {
      current: Number(latestBankroll?.bankroll_units ?? process.env.DEFAULT_BANKROLL_UNITS ?? 100),
      unitsWonLost: totalProfit,
      dailyProfit,
      weeklyProfit,
      monthlyProfit
    },
    backtest: {
      bySeason: emptyPoints(["2022", "2023", "2024", "2025", "2026"]),
      byEdgeBucket: emptyPoints(["4-6%", "6-8%", "8-10%", "10%+"]),
      byConfidence: emptyPoints(["Low", "Medium", "High"])
    }
  };
}

