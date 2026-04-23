/**
 * Thin fetch wrapper for the PWM REST API.
 *
 * Always runs server-side (App Router RSCs) so the API URL can be an
 * internal hostname (e.g. "api:8000" inside Docker) and cookies never leak.
 */

const BASE = process.env.PWM_API_URL || 'http://localhost:8000';
const REVALIDATE = 60; // seconds; matches API Cache-Control.

async function get<T>(path: string): Promise<T | null> {
  const url = path.startsWith('http') ? path : `${BASE}${path}`;
  try {
    const res = await fetch(url, { next: { revalidate: REVALIDATE } });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export type ActivityEntry = {
  kind: string;
  timestamp: number;
  block_number: number;
  primary_hash: string | null;
  actor: string | null;
  layer: number | null;
  amount: string | null;
  secondary_hash: string | null;
  extra: string | null;
};

export type Overview = {
  counts: {
    principles: number;
    specs: number;
    benchmarks: number;
    certificates: number;
    draws: number;
    registered_benchmarks?: number;
    mints?: number;
    stakes?: number;
  };
  active_principles: number;
  total_pool_wei: string;
  recent_draws: Array<{
    cert_hash: string;
    benchmark_hash: string;
    rank: number;
    draw_amount: string;
    settled_at: number;
  }>;
  recent_activity: ActivityEntry[];
};

export type PrincipleSummary = {
  artifact_id: string;
  title: string;
  domain: string;
  sub_domain?: string;
  difficulty_delta?: number;
  difficulty_tier?: string;
  L_DAG?: number;
  forward_model?: string;
  active_spec_count?: number;
  active_benchmark_count?: number;
  epsilon_center?: string;
};

export type PrincipleDetail = {
  principle: any;
  specs: Array<{ artifact_id: string; title: string; spec_type: string; d_spec?: number }>;
  treasury_balance_wei: string | null;
  registered_benchmarks: Array<{
    benchmark_hash: string;
    principle_id: string;
    rho: string;
    registered_at: number;
    removed_at: number | null;
  }>;
  chain_meta: { principle_id: string; delta: string | null; promoted: number | null; updated_at: number } | null;
  total_minted_wei: string;
};

export type BenchmarkSummary = {
  artifact_id: string;
  parent_l2?: string;
  parent_l1?: string;
  title?: string;
  rho?: number;
  omega_tier?: Record<string, unknown>;
  epsilon?: number;
  domain?: string;
};

export type BenchmarksList = {
  genesis: BenchmarkSummary[];
  chain: Array<{ hash: string; creator: string; timestamp: number; block_number: number; pool_balance_wei: string | null; artifact_id?: string | null }>;
};

export type BenchmarkDetail = {
  genesis: any;
  chain: any;
  leaderboard: Array<any>;
  pool_balance_wei: string | null;
};

export type CertDetail = {
  certificate: {
    cert_hash: string;
    benchmark_hash: string;
    submitter: string;
    q_int: number;
    status: number;
    submitted_at: number;
    finalized_rank?: number;
    challenger?: string;
    challenge_upheld?: number;
    draw_rank?: number;
    draw_amount?: string;
    rollover_remaining?: string;
    settled_at?: number;
    ac_addr?: string;
    ac_amount?: string;
    cp_addr?: string;
    cp_amount?: string;
    treasury_amount?: string;
  };
  benchmark_chain: any;
  benchmark_genesis: any;
  s_gates: { S1: string; S2: string; S3: string; S4: string };
};

export type Pools = {
  pools: Array<{ benchmark_hash: string; balance: string }>;
  treasury: Array<{ principle_id: string; balance: string }>;
};

export type Bounty = {
  slug: string;
  title: string;
  amount_pwm: number | null;
  summary: string;
  spec_path: string;
};

export const api = {
  overview: () => get<Overview>('/api/overview'),
  principles: () => get<{ genesis: PrincipleSummary[]; chain: any[]; domains: string[] }>('/api/principles'),
  principle: (id: string) => get<PrincipleDetail>(`/api/principles/${encodeURIComponent(id)}`),
  benchmarks: () => get<BenchmarksList>('/api/benchmarks'),
  benchmark: (ref: string) => get<BenchmarkDetail>(`/api/benchmarks/${encodeURIComponent(ref)}`),
  pools: () => get<Pools>('/api/pools'),
  cert: (hash: string) => get<CertDetail>(`/api/cert/${encodeURIComponent(hash)}`),
  leaderboard: (hash: string) => get<{ benchmark_hash: string; entries: any[] }>(`/api/leaderboard/${encodeURIComponent(hash)}`),
  bounties: () => get<{ bounties: Bounty[] }>('/api/bounties'),
  network: () => get<{ network: string; addresses: Record<string, string> }>('/api/network'),
  activity: (limit = 50) => get<{ activity: ActivityEntry[] }>(`/api/activity?limit=${limit}`),
  match: (params: {
    prompt?: string;
    domain?: string;
    modality?: string;
    h?: number;
    w?: number;
    noise?: number;
  }) => {
    const q = new URLSearchParams();
    if (params.prompt) q.set('prompt', params.prompt);
    if (params.domain) q.set('domain', params.domain);
    if (params.modality) q.set('modality', params.modality);
    if (params.h !== undefined) q.set('h', String(params.h));
    if (params.w !== undefined) q.set('w', String(params.w));
    if (params.noise !== undefined) q.set('noise', String(params.noise));
    return get<MatchResult>(`/api/match?${q.toString()}`);
  },
};

export type MatchCandidate = {
  benchmark_id: string;
  rank: number;
  score: number;
  tier: string | null;
  rationale: string;
};

export type MatchResult = {
  candidates: MatchCandidate[];
  clarifying_question: string | null;
  confidence_floor_hit: boolean;
};
