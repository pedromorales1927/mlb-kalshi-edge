import type { BoardGame } from "@/app/lib/types";
import { formatPercent, formatSignedPercent } from "@/app/lib/format";

type Props = {
  board: BoardGame[];
};

export function TodaysBoard({ board }: Props) {
  return (
    <section className="section">
      <div className="section-title">
        <h2>Today&apos;s MLB Board</h2>
        <span>Every game on the slate</span>
      </div>
      <div className="table-shell">
        <table>
          <thead>
            <tr>
              <th>Game</th>
              <th>Starters</th>
              <th>Predicted Winner</th>
              <th>Win Probability</th>
              <th>Edge</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {board.map((game) => (
              <tr key={game.gameId}>
                <td>
                  <strong>
                    {game.awayTeam} @ {game.homeTeam}
                  </strong>
                </td>
                <td>
                  <span>{game.awayPitcher ?? "TBD"}</span>
                  <span className="muted"> vs </span>
                  <span>{game.homePitcher ?? "TBD"}</span>
                  <span className={game.startersConfirmed ? "pill good" : "pill warn"}>
                    {game.startersConfirmed ? "Confirmed" : "Unconfirmed"}
                  </span>
                </td>
                <td>{game.predictedWinner ? (game.predictedWinner === "home" ? game.homeTeam : game.awayTeam) : "N/A"}</td>
                <td>{formatPercent(game.winProbability)}</td>
                <td>{formatSignedPercent(game.edge)}</td>
                <td>
                  <span className={`confidence ${game.confidenceRating ?? "low"}`}>
                    {game.confidenceRating ?? "low"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

