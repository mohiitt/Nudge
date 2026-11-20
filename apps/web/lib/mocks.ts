import type {
  AccountDeepDive,
  Approval,
  DailyBriefing,
  MockBundle,
} from "./types";

const CSM_ID = "csm_demo_001";

function isoDaysFromNow(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export function buildMockBundle(csmId = CSM_ID): MockBundle {
  const accounts = [
    {
      account_id: "acc_acme",
      name: "Acme Analytics",
      industry: "SaaS",
      arr: 120000,
      plan_tier: "Growth",
      renewal_date: isoDaysFromNow(28),
      health_score: 0.42,
      status: "churn_risk" as const,
      owner_csm_id: csmId,
    },
    {
      account_id: "acc_bright",
      name: "BrightPath Health",
      industry: "Healthcare",
      arr: 86000,
      plan_tier: "Pro",
      renewal_date: isoDaysFromNow(90),
      health_score: 0.71,
      status: "active" as const,
      owner_csm_id: csmId,
    },
    {
      account_id: "acc_northstar",
      name: "Northstar Retail",
      industry: "Retail",
      arr: 210000,
      plan_tier: "Enterprise",
      renewal_date: isoDaysFromNow(45),
      health_score: 0.55,
      status: "expansion" as const,
      owner_csm_id: csmId,
    },
  ];

  const risks = [
    {
      account_id: "acc_acme",
      owner_csm_id: csmId,
      name: "Acme Analytics",
      arr: 120000,
      renewal_date: accounts[0].renewal_date,
      usage_delta_30d: -0.32,
      open_tickets: 3,
      days_to_renewal: 28,
      failed_payments: 1,
      risk_score: 0.78,
      reasons: ["Usage down 32% vs prior 30d", "Renewal in 28 days", "1 failed payment"],
    },
    {
      account_id: "acc_bright",
      owner_csm_id: csmId,
      name: "BrightPath Health",
      arr: 86000,
      renewal_date: accounts[1].renewal_date,
      usage_delta_30d: -0.08,
      open_tickets: 1,
      days_to_renewal: 90,
      failed_payments: 0,
      risk_score: 0.41,
      reasons: ["Slight usage dip", "1 open ticket"],
    },
    {
      account_id: "acc_northstar",
      owner_csm_id: csmId,
      name: "Northstar Retail",
      arr: 210000,
      renewal_date: accounts[2].renewal_date,
      usage_delta_30d: 0.12,
      open_tickets: 2,
      days_to_renewal: 45,
      failed_payments: 0,
      risk_score: 0.52,
      reasons: ["Open tickets on SSO", "Expansion signal vs support load"],
    },
  ];

  const briefing: DailyBriefing = {
    csm_id: csmId,
    generated_at: new Date().toISOString(),
    summary: "Three accounts need attention; Acme is highest risk before renewal.",
    items: accounts.map((account, i) => ({
      account,
      risk: risks[i],
      top_reasons: risks[i].reasons,
      recommended_next_step: "Review hybrid context and propose outreach plan",
    })),
  };

  const approvals: Approval[] = [
    {
      approval_id: "apr_001",
      csm_id: csmId,
      account_id: "acc_acme",
      action_type: "external_email",
      title: "Draft: check-in before renewal",
      description: "Email draft pending approval — will not send until approved.",
      payload: { to: "csm-contact@acme.example", subject: "Quick check-in" },
      status: "pending",
      created_at: new Date(Date.now() - 2 * 3600_000).toISOString(),
    },
  ];

  const deepDives: Record<string, AccountDeepDive> = {};
  for (let i = 0; i < accounts.length; i++) {
    const account = accounts[i];
    const risk = risks[i];
    deepDives[account.account_id] = {
      account,
      risk,
      usage_delta_30d: risk.usage_delta_30d,
      open_tickets: risk.open_tickets,
      recent_tickets: [
        {
          chunk_id: `chk_${account.account_id}_0`,
          account_id: account.account_id,
          owner_csm_id: csmId,
          ticket_id: `tkt_${account.account_id}_0`,
          category: "support",
          sentiment: "negative",
          created_at: new Date().toISOString(),
          text_redacted: "Customer reported friction with recent release.",
          similarity: 0.91,
        },
      ],
      similar_accounts: accounts
        .filter((a) => a.account_id !== account.account_id)
        .map((a, idx) => ({
          account_id: a.account_id,
          name: a.name,
          similarity: 0.8 - idx * 0.1,
          intervention_summary: "Scheduled QBR + success plan email",
          outcome: "improved" as const,
        })),
      recommendations: [
        {
          recommendation_id: `rec_${account.account_id}`,
          account_id: account.account_id,
          owner_csm_id: csmId,
          title: "Propose check-in plan",
          rationale: risk.reasons.join("; "),
          suggested_actions: ["draft_message", "create_task", "escalate"],
          priority: risk.risk_score >= 0.6 ? "high" : "medium",
          risk_score: risk.risk_score,
        },
      ],
      recent_activities: [],
    };
  }

  return {
    csm: {
      csm_id: csmId,
      email: "alex@nudge.local",
      full_name: "Alex Rivera",
      timezone: "America/Los_Angeles",
    },
    preferences: {
      csm_id: csmId,
      preferred_channel: "email",
      briefing_hour_local: 8,
      risk_threshold: 0.6,
    },
    briefing,
    accounts,
    approvals,
    deepDives,
  };
}
