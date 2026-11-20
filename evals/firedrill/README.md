# Firedrill drills for Nudge

Apply event code **TOKENSAND** under Firedrill Billing for extra non-expiring credits.

## Setup

```bash
npm i -g firedrill-run   # Node 22, 24, or 26
firedrill init
```

Add MCP `https://mcp.firedrill.run` in Cursor and
`npx skills add firedrill-tools/firedrill-skills`.

## Local plan

`plans/local.yaml` drives `http.v1` against the agent:

```
POST http://localhost:8000/chat
{"message":"...","session":"..."} → {"reply":"..."}
```

Start the agent with `MOCK_MODE=true` first.

## Contents

| Path | Role |
|------|------|
| `descriptor.yaml` | Project descriptor |
| `plans/local.yaml` | Local http.v1 plan |
| `world/` | Synthetic hubspot / stripe / gmail / slack |
| `scenarios/` | 8 edge-case scenarios |
| `evaluations/` | Assertions on **state changes**, not reply wording |

Review credit estimate before each `firedrill apply`.
