"use client";

import { useEffect, useState } from "react";
import { decideApproval, getApprovals } from "../../lib/api";
import type { Approval } from "../../lib/types";

export default function ApprovalsPage() {
  const [items, setItems] = useState<Approval[]>([]);
  const [busy, setBusy] = useState<string | null>(null);

  async function load() {
    setItems(await getApprovals());
  }

  useEffect(() => {
    void load();
  }, []);

  async function onDecide(id: string, decision: "approved" | "rejected") {
    setBusy(id);
    await decideApproval(id, decision);
    await load();
    setBusy(null);
  }

  return (
    <main className="page">
      <h1>Approvals</h1>
      <p className="sub">Sensitive actions wait here. Email drafts never send until you approve.</p>
      <div className="list">
        {items.length === 0 && <p className="meta">No pending approvals.</p>}
        {items.map((a) => (
          <div key={a.approval_id} className="list-row">
            <div>
              <h2>{a.title}</h2>
              <p>
                {a.action_type}
                {a.account_id ? ` · ${a.account_id}` : ""} — {a.description}
              </p>
              <p className="meta">
                {a.status}
                {a.decided_at ? ` · decided ${a.decided_at}` : ""}
              </p>
              {a.status === "pending" && (
                <div className="actions-row">
                  <button
                    className="btn"
                    disabled={busy === a.approval_id}
                    onClick={() => onDecide(a.approval_id, "approved")}
                  >
                    Approve
                  </button>
                  <button
                    className="btn danger"
                    disabled={busy === a.approval_id}
                    onClick={() => onDecide(a.approval_id, "rejected")}
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
