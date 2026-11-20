# Amplitude event list (Nudge)

All product and agent telemetry uses Amplitude HTTP V2. On the Free plan, batch
**at most 10 events per request**. Use `user_id = csm_id` and `device_id` /
`session_id` when available. Never put PII (email bodies, names of contacts) in
event properties — use account/ticket IDs and redacted summaries.

## Agent lifecycle

| Event | When | Key properties |
|-------|------|----------------|
| `agent.session_started` | Chat / briefing session opens | `session_id`, `source` (`web` \| `firedrill` \| `api`) |
| `agent.message_received` | User message accepted | `session_id`, `message_len` |
| `agent.tool_called` | Tool invoked in Claude loop | `tool_name`, `account_id?`, `latency_ms` |
| `agent.tool_failed` | Tool raised / timed out | `tool_name`, `error_class` |
| `agent.reply_sent` | Reply returned to client | `session_id`, `reply_len`, `action_count` |

## Risk & briefing

| Event | When | Key properties |
|-------|------|----------------|
| `briefing.generated` | Daily briefing built | `item_count`, `high_risk_count` |
| `briefing.item_opened` | CSM opens an account from briefing | `account_id`, `risk_score` |
| `account.risk_scored` | Health/scoring job updates an account | `account_id`, `risk_score`, `usage_delta_30d` |
| `account.deep_dive_viewed` | Deep-dive page loaded | `account_id` |
| `similar_accounts.retrieved` | Vector similar-accounts tool | `account_id`, `result_count` |

## Approvals & actions

| Event | When | Key properties |
|-------|------|----------------|
| `approval.requested` | Sensitive action → `approval_requests` | `approval_id`, `action_type`, `account_id?` |
| `approval.decided` | CSM approves or rejects | `approval_id`, `decision`, `action_type` |
| `action.executed` | Action Gateway succeeds | `action_id`, `action_type`, `adapter` |
| `action.failed` | Action Gateway fails | `action_id`, `action_type`, `error_class` |
| `action.skipped` | Policy blocked / not owned | `action_type`, `reason` |

## Interventions & outcomes

| Event | When | Key properties |
|-------|------|----------------|
| `intervention.recorded` | Intervention row written | `intervention_id`, `account_id`, `action_type` |
| `intervention.outcome_measured` | Outcome job updates result | `intervention_id`, `outcome`, `days_since` |

## Ingestion / jobs (ops)

| Event | When | Key properties |
|-------|------|----------------|
| `job.health_scoring_completed` | Scoring job finishes | `accounts_scored`, `duration_ms` |
| `job.embed_batch_completed` | SIE batch embed finishes | `rows_embedded`, `cache_hits` |
| `job.outcome_tracking_completed` | Outcome tracker finishes | `updated_count` |

## Firedrill

| Event | When | Key properties |
|-------|------|----------------|
| `firedrill.scenario_started` | Scenario begins | `scenario_id` |
| `firedrill.scenario_passed` | Eval assertions pass | `scenario_id` |
| `firedrill.scenario_failed` | Eval assertions fail | `scenario_id`, `failed_checks` |

## Property conventions

- `csm_id` / `user_id`: always set for CSM-scoped events.
- `account_id`: set when the event is account-scoped; omit otherwise.
- `source`: `web` | `agent` | `job` | `firedrill` | `ingest`.
- Timestamps: Amplitude `time` as epoch ms; do not rely on server receipt time for ordering.
