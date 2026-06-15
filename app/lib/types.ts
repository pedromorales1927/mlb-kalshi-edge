export type ConfidenceRating = "low" | "medium" | "high";

export type TopBet = {
  id: string;
  rank: number;
  game: string;
  gameTime: string | null;
  recommendedSide: "home" | "away";
  recommendedTeam: string;
  modelProbability: number;
  kalshiProbability: number;
  edge: number;
  expectedValue: number;
  recommendedUnits: number;
  confidenceRating: ConfidenceRating;
  confidenceScore: number;
  reason: string;
};

export type BoardGame = {
  gameId: string;
  gameDate: string;
  gameTime: string | null;
  homeTeam: string;
  awayTeam: string;
  homePitcher: string | null;
  awayPitcher: string | null;
  startersConfirmed: boolean;
  predictedWinner: "home" | "away" | null;
  winProbability: number | null;
  edge: number | null;
  confidenceRating: ConfidenceRating | null;
};

export type PerformancePoint = {
  label: string;
  roi: number;
  profit: number;
  brier: number;
};

export type DashboardData = {
  generatedAt: string;
  slateDate: string;
  topBets: TopBet[];
  board: BoardGame[];
  performance: {
    historicalRoi: number;
    winRate: number;
    clv: number;
    totalProfit: number;
    accuracy: number;
    brierScore: number;
    points: PerformancePoint[];
  };
  bankroll: {
    current: number;
    unitsWonLost: number;
    dailyProfit: number;
    weeklyProfit: number;
    monthlyProfit: number;
  };
  backtest: {
    bySeason: PerformancePoint[];
    byEdgeBucket: PerformancePoint[];
    byConfidence: PerformancePoint[];
  };
};

