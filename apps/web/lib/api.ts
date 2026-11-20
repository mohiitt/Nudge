import { buildMockBundle } from "./mocks";
import type {
  AccountDeepDive,
  Approval,
  ChatResponse,
  DailyBriefing,
} from "./types";

const AGENT_URL = process.env.NEXT_PUBLIC_AGENT_URL || "http://localhost:8000";
const CSM_ID = process.env.NEXT_PUBLIC_CSM_ID || "csm_demo_001";

type FetchResult<T> =
  | { ok: true; data: T }
  | { ok: false; status: number; denied: boolean };

async function fetchJson<T>(path: string, init?: RequestInit): Promise<FetchResult<T>> {
  try {
    const res = await fetch(`${AGENT_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
      cache: "no-store",
    });
    if (!res.ok) {
      return { ok: false, status: res.status, denied: res.status === 403 };
    }
    return { ok: true, data: (await res.json()) as T };
  } catch {
    return { ok: false, status: 0, denied: false };
  }
}

export async function getBriefing(csmId = CSM_ID): Promise<DailyBriefing> {
  const result = await fetchJson<DailyBriefing>(`/briefing/${csmId}`);
  if (result.ok) return result.data;
  return buildMockBundle(csmId).briefing;
}

export async function getAccount(accountId: string, csmId = CSM_ID): Promise<AccountDeepDive | null> {
  const result = await fetchJson<AccountDeepDive>(`/accounts/${accountId}?csm_id=${csmId}`);
  if (result.ok) return result.data;
  // Never mask ownership denials with mock data
  if (result.denied) return null;
  return buildMockBundle(csmId).deepDives[accountId] ?? null;
}

export async function getApprovals(csmId = CSM_ID): Promise<Approval[]> {
  const result = await fetchJson<Approval[]>(`/approvals?csm_id=${csmId}`);
  if (result.ok) return result.data;
  return buildMockBundle(csmId).approvals;
}

export async function decideApproval(
  approvalId: string,
  decision: "approved" | "rejected",
  csmId = CSM_ID,
): Promise<Approval | null> {
  const result = await fetchJson<Approval>(`/approvals/${approvalId}/decide`, {
    method: "POST",
    body: JSON.stringify({ decision, decided_by: csmId, csm_id: csmId }),
  });
  return result.ok ? result.data : null;
}

export async function sendChat(message: string, session?: string): Promise<ChatResponse> {
  const result = await fetchJson<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message, session: session || "web", csm_id: CSM_ID }),
  });
  if (result.ok) return result.data;
  return {
    reply: `(offline mock) Nudge received: ${message.slice(0, 200)}`,
    session: session || "web",
    actions: [],
    approvals: [],
  };
}

export { CSM_ID, AGENT_URL };
