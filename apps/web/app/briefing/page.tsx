import Link from "next/link";
import { getBriefing } from "../../lib/api";

export default async function BriefingPage() {
  const briefing = await getBriefing();

  return (
    <main className="page">
      <h1>Daily briefing</h1>
      <p className="sub">{briefing.summary}</p>
      <div className="list">
        {briefing.items.map((item) => (
          <Link
            key={item.account.account_id}
            href={`/accounts/${item.account.account_id}`}
            className="list-row"
          >
            <div>
              <h2>{item.account.name}</h2>
              <p>{item.top_reasons.join(" · ") || item.recommended_next_step}</p>
            </div>
            <div className="risk">{item.risk.risk_score.toFixed(2)}</div>
          </Link>
        ))}
      </div>
    </main>
  );
}
