import Link from "next/link";
import { notFound } from "next/navigation";
import { getAccount } from "../../../lib/api";

export default async function AccountPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const dive = await getAccount(id);
  if (!dive) notFound();

  return (
    <main className="page">
      <p className="meta">
        <Link href="/briefing">Briefing</Link> / {dive.account.account_id}
      </p>
      <h1>{dive.account.name}</h1>
      <p className="sub">
        Risk {dive.risk.risk_score.toFixed(2)} · usage Δ30d {(dive.usage_delta_30d * 100).toFixed(0)}% ·{" "}
        {dive.open_tickets} open tickets
      </p>

      <div className="stack">
        <section>
          <h2 className="section-title">Why it surfaced</h2>
          <p className="lede" style={{ margin: 0 }}>
            {dive.risk.reasons.join(" · ") || "Hybrid risk signals."}
          </p>
        </section>

        <section>
          <h2 className="section-title">Recent ticket themes</h2>
          <div className="list">
            {dive.recent_tickets.map((t) => (
              <div key={t.chunk_id} className="list-row">
                <div>
                  <h2>{t.category || "ticket"}</h2>
                  <p>{t.text_redacted}</p>
                </div>
                <div className="meta">{t.sentiment}</div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="section-title">Similar accounts</h2>
          <div className="list">
            {dive.similar_accounts.map((s) => (
              <div key={s.account_id} className="list-row">
                <div>
                  <h2>{s.name}</h2>
                  <p>
                    {s.intervention_summary} · outcome {s.outcome}
                  </p>
                </div>
                <div className="risk">{s.similarity.toFixed(2)}</div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="section-title">Recommended next step</h2>
          {dive.recommendations.map((r) => (
            <div key={r.recommendation_id}>
              <p style={{ margin: "0 0 0.5rem" }}>
                <strong>{r.title}</strong> — {r.rationale}
              </p>
              <p className="meta">{r.suggested_actions.join(" → ")}</p>
            </div>
          ))}
          <div className="cta" style={{ marginTop: "1.25rem" }}>
            <Link href="/chat">Ask Nudge to draft a plan</Link>
            <Link className="ghost" href="/approvals">
              Approvals inbox
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
