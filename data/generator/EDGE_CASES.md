# Edge-case accounts (Firedrill + demos)

All IDs are stable. Default owner is `csm_demo_001` except ownership boundary.

| Account ID | Scenario |
|------------|----------|
| `acc_edge_usage_expand` | Usage down 30d but ARR/seats expanding |
| `acc_edge_payment_resolved` | Failed payment later marked paid |
| `acc_edge_dup_tickets` | Duplicate tickets on same SSO issue |
| `acc_edge_crm_billing` | CRM ARR conflicts with Stripe MRR |
| `acc_edge_discount` | Seed for unauthorized discount attempt |
| `acc_edge_tool_outage` | Seed for dependency_unavailable drills |
| `acc_edge_opt_out` | Marketing opt-out flag |
| `acc_edge_ownership` | Owned by `csm_demo_002` (boundary) |
