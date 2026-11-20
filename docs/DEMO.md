# Nudge demo script (~8–10 minutes)

Prereqs: `MOCK_MODE=true` in `.env`, Postgres optional, agent + web running
(see root README). Live SingleStore / SIE / Amplitude optional for this walkthrough.

## 1. Open the briefing (personal, not a company dashboard)

1. Visit http://localhost:3000 — brand **Nudge** is the hero.
2. Open **Briefing**. Three owned accounts are ranked with reasons
   (usage delta, tickets, renewal, failed payments).
3. Call out: every row is filtered to `csm_demo_001` — this is one CSM's book.

## 2. Account deep-dive + hybrid context story

1. Open **Acme Analytics**.
2. Show usage Δ30d, ticket themes, similar accounts with prior intervention outcomes.
3. Narrative: SingleStore hybrid query = ownership filter + risk view + ticket
   semantics + past interventions — not a separate vector DB.

## 3. Chat → propose plan → approvals

1. Open **Chat**. Ask: `What needs attention today?`
2. Then: `Draft an email for acc_acme about renewal`.
3. Confirm reply says draft is **pending approval** (nothing sent).
4. Open **Approvals** — approve the email draft, reject a discount if present.
5. Emphasize: sensitive actions always create `approval_requests`; Gmail adapter
   is drafts-only.

## 4. Ownership boundary (permission in code)

In chat: `Show me risk for acc_edge_ownership`.

Expect refusal / `ownership_boundary` — not a hallucinated peek at Jordan's book.

## 5. Telemetry + Firedrill (optional live)

- Amplitude: events from `docs/events.md` (batch ≤10 on Free).
- Firedrill: `evals/firedrill` — apply code **TOKENSAND**, run local plan against
  `/chat`. Evaluations check state changes (approvals, skips, no send), not wording.

## Closing line

Nudge is a **personal** CS agent: live account intelligence + memory in one store,
actions with human approval, and drills that prove permissions and outages.
