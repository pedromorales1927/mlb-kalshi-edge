import { TrendingUp } from "lucide-react";
import type { TopBet } from "@/app/lib/types";
import { formatPercent, formatSignedPercent } from "@/app/lib/format";

type Props = {
  bets: TopBet[];
};

export function TopBets({ bets }: Props) {
  if (bets.length === 0) {
    return (
      <section className="section">
        <div className="section-title">
          <h2>Top 5 Bets Today</h2>
        </div>
        <div className="empty-state">No qualifying positive EV bets meet the current filters.</div>
      </section>
    );
  }

  return (
    <section className="section top-section">
      <div className="section-title">
        <h2>Top 5 Bets Today</h2>
        <span>Ranked by edge and risk-adjusted expected value</span>
      </div>
      <div className="top-grid">
        {bets.map((bet) => (
          <article className={`top-card ${bet.confidenceRating}`} key={bet.id}>
            <div className="top-card-header">
              <div className="rank">#{bet.rank}</div>
              <div>
                <h3>{bet.recommendedTeam}</h3>
                <p>{bet.game}</p>
              </div>
              <TrendingUp size={22} />
            </div>
            <div className="bet-metrics">
              <div>
                <span>Model</span>
                <strong>{formatPercent(bet.modelProbability)}</strong>
              </div>
              <div>
                <span>Kalshi</span>
                <strong>{formatPercent(bet.kalshiProbability)}</strong>
              </div>
              <div>
                <span>Edge</span>
                <strong>{formatSignedPercent(bet.edge)}</strong>
              </div>
              <div>
                <span>EV</span>
                <strong>{formatSignedPercent(bet.expectedValue)}</strong>
              </div>
              <div>
                <span>Units</span>
                <strong>{bet.recommendedUnits.toFixed(2)}</strong>
              </div>
              <div>
                <span>Confidence</span>
                <strong>{bet.confidenceRating}</strong>
              </div>
            </div>
            <p className="reason">{bet.reason}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

