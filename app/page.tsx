"use client";

import useSWR from "swr";
import { Activity, Banknote, Gauge, RefreshCw, Target } from "lucide-react";
import { TopBets } from "./components/TopBets";
import { TodaysBoard } from "./components/TodaysBoard";
import { BucketBarChart, RoiAreaChart } from "./components/Charts";
import { MetricCard } from "./components/MetricCard";
import type { DashboardData } from "./lib/types";
import { formatPercent, formatUnits } from "./lib/format";

const fetcher = async (url: string): Promise<DashboardData> => {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error("Failed to load dashboard data");
  return response.json();
};

export default function DashboardPage() {
  const { data, error, isLoading, mutate } = useSWR<DashboardData>("/api/dashboard", fetcher, {
    refreshInterval: 60_000,
    revalidateOnFocus: true
  });

  if (isLoading) {
    return <main className="page"><div className="empty-state">Loading MLB edge board...</div></main>;
  }

  if (error || !data) {
    return (
      <main className="page">
        <div className="empty-state danger">Unable to load dashboard data.</div>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="app-header">
        <div>
          <h1>MLB Kalshi Edge</h1>
          <p>Slate {data.slateDate} · Updated {new Date(data.generatedAt).toLocaleTimeString()}</p>
        </div>
        <button className="icon-button" onClick={() => mutate()} aria-label="Refresh dashboard">
          <RefreshCw size={18} />
        </button>
      </header>

      <TopBets bets={data.topBets} />

      <TodaysBoard board={data.board} />

      <section className="section">
        <div className="section-title">
          <h2>Model Performance</h2>
          <span>Betting outcomes and probability calibration</span>
        </div>
        <div className="metric-grid">
          <MetricCard label="Historical ROI" value={formatPercent(data.performance.historicalRoi)} />
          <MetricCard label="Win Rate" value={formatPercent(data.performance.winRate)} />
          <MetricCard label="CLV" value={formatPercent(data.performance.clv)} />
          <MetricCard label="Total Profit" value={formatUnits(data.performance.totalProfit)} />
          <MetricCard label="Accuracy" value={formatPercent(data.performance.accuracy)} />
          <MetricCard label="Brier Score" value={data.performance.brierScore.toFixed(3)} />
        </div>
        <div className="two-column">
          <div>
            <div className="panel-title"><Activity size={18} /> Profit Trend</div>
            <RoiAreaChart data={data.performance.points} />
          </div>
          <div>
            <div className="panel-title"><Gauge size={18} /> ROI by Edge Bucket</div>
            <BucketBarChart data={data.backtest.byEdgeBucket} />
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-title">
          <h2>Bankroll Tracker</h2>
          <span>Exposure and realized movement</span>
        </div>
        <div className="metric-grid">
          <MetricCard label="Current Bankroll" value={`${data.bankroll.current.toFixed(2)}u`} />
          <MetricCard label="Units Won/Lost" value={formatUnits(data.bankroll.unitsWonLost)} />
          <MetricCard label="Daily Profit" value={formatUnits(data.bankroll.dailyProfit)} />
          <MetricCard label="Weekly Profit" value={formatUnits(data.bankroll.weeklyProfit)} />
          <MetricCard label="Monthly Profit" value={formatUnits(data.bankroll.monthlyProfit)} />
        </div>
      </section>

      <section className="section">
        <div className="section-title">
          <h2>Backtest Results</h2>
          <span>Historical ROI and model behavior</span>
        </div>
        <div className="three-column">
          <div>
            <div className="panel-title"><Target size={18} /> ROI by Season</div>
            <BucketBarChart data={data.backtest.bySeason} />
          </div>
          <div>
            <div className="panel-title"><Gauge size={18} /> ROI by Confidence</div>
            <BucketBarChart data={data.backtest.byConfidence} />
          </div>
          <div>
            <div className="panel-title"><Banknote size={18} /> Historical Performance</div>
            <RoiAreaChart data={data.performance.points} />
          </div>
        </div>
      </section>
    </main>
  );
}

