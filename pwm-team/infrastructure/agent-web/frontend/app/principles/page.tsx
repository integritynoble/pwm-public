import Link from 'next/link';
import { api } from '@/lib/api';
import { ApiDown, Empty } from '@/components/Empty';

type Tier = 'mineable' | 'stub' | 'all';

function isTier(value: string | undefined): Tier {
  return value === 'stub' || value === 'all' ? value : 'mineable';
}

function tierBadge(tier: string | undefined) {
  if (tier === 'founder_vetted') {
    return <span className="pwm-pill !text-emerald-300 !border-emerald-500/40">★ Founder-vetted</span>;
  }
  if (tier === 'community_proposed') {
    return <span className="pwm-pill !text-cyan-300 !border-cyan-500/40">✓ Community-vetted</span>;
  }
  return <span className="pwm-pill !text-slate-500 !border-slate-700">📋 Stub — not mineable</span>;
}

export default async function PrinciplesPage({
  searchParams,
}: {
  searchParams: Promise<{
    domain?: string; q?: string; tier?: string;
    carrier?: string; problem_class?: string; noise_model?: string;
  }>;
}) {
  const params = await searchParams;
  const tier: Tier = isTier(params.tier);
  const data = await api.principles({
    tier,
    carrier: params.carrier,
    problem_class: params.problem_class,
    noise_model: params.noise_model,
  });
  if (!data) return <ApiDown />;

  const domainFilter = params.domain;
  const q = (params.q ?? '').trim().toLowerCase();
  const filtered = data.genesis.filter((p) => {
    if (domainFilter && p.domain !== domainFilter) return false;
    if (q) {
      const haystack = [p.artifact_id, p.title, p.domain, p.sub_domain, p.forward_model]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      if (!haystack.includes(q)) return false;
    }
    return true;
  });

  const counts = data.tier_counts;
  const mineableCount = counts.founder_vetted + counts.community_proposed;

  // Common URL param builder so all pills + form preserve the user's state
  const buildHref = (overrides: Record<string, string | undefined>) => {
    const qs = new URLSearchParams();
    const fields: Record<string, string | undefined> = {
      tier, q: params.q, domain: domainFilter,
      carrier: params.carrier, problem_class: params.problem_class,
      noise_model: params.noise_model, ...overrides,
    };
    for (const [k, v] of Object.entries(fields)) {
      if (v) qs.set(k, v);
    }
    return `/principles?${qs.toString()}`;
  };

  const tierTab = (label: string, value: Tier, count: number) => {
    const active = tier === value;
    return (
      <Link
        href={buildHref({ tier: value })}
        className={`pwm-pill ${active ? '!text-white !border-pwm-accent' : ''}`}
      >
        {label} <span className="text-pwm-muted">({count})</span>
      </Link>
    );
  };

  const facetPill = (
    axis: 'carrier' | 'problem_class' | 'noise_model',
    value: string,
    count: number,
  ) => {
    const active = (params[axis] ?? '') === value;
    // Click an active pill to clear it; click an inactive pill to select it
    const overrides = { [axis]: active ? undefined : value };
    return (
      <Link
        key={`${axis}-${value}`}
        href={buildHref(overrides)}
        className={`pwm-pill ${active ? '!text-white !border-pwm-accent' : ''}`}
      >
        {value} <span className="text-pwm-muted">({count})</span>
      </Link>
    );
  };

  // Sort facet values by descending count and keep top 8 per axis (everything else
  // is a long tail of single-instance values that just clutter the UI)
  const topFacets = (axis: 'carrier' | 'problem_class' | 'noise_model'): [string, number][] => {
    const m = data.facet_counts?.[axis] ?? {};
    return Object.entries(m).filter(([, n]) => n >= 3).sort(([, a], [, b]) => b - a).slice(0, 8);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-3xl font-bold tracking-tight">Principles</h1>
        <div className="text-sm text-pwm-muted">
          {filtered.length} of {data.genesis.length} shown
        </div>
      </div>

      <div className="pwm-card border-slate-700">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-pwm-muted mr-2">View:</span>
          {tierTab('Mineable', 'mineable', mineableCount)}
          {tierTab('Claim Board', 'stub', counts.stub)}
          {tierTab('All', 'all', counts.total)}
        </div>
        <p className="text-xs text-pwm-muted mt-3">
          {tier === 'mineable' && (
            <>
              <strong className="text-emerald-300">Mineable</strong> — Principles registered on-chain with funded reward
              pools. Submitting a cert against these earns PWM.
            </>
          )}
          {tier === 'stub' && (
            <>
              <strong className="text-slate-300">Claim Board</strong> — scientifically-declared inventory awaiting
              external contributors. Each stub is an open invitation: author the reference solver + dataset, open a PR,
              and earn the registration bounty. Not mineable until promoted to Tier 1/2 by 3-of-5 multisig.
            </>
          )}
          {tier === 'all' && (
            <>Combined view — mineable Principles ranked first, claim-board stubs after, all rendered with their tier badge.</>
          )}
        </p>
      </div>

      <form action="/principles" method="GET" className="flex gap-2">
        <input type="hidden" name="tier" value={tier} />
        {domainFilter && <input type="hidden" name="domain" value={domainFilter} />}
        {params.carrier && <input type="hidden" name="carrier" value={params.carrier} />}
        {params.problem_class && <input type="hidden" name="problem_class" value={params.problem_class} />}
        {params.noise_model && <input type="hidden" name="noise_model" value={params.noise_model} />}
        <input
          type="search"
          name="q"
          defaultValue={q}
          placeholder="Search by ID, title, domain, or forward model…"
          className="flex-1 bg-slate-950/60 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-pwm-accent"
        />
        <button type="submit" className="pwm-pill !border-pwm-accent !text-pwm-accent px-4">
          Search
        </button>
      </form>

      {/* Faceted physics filters — click to toggle, click again to clear */}
      {data.facet_counts && (
        <div className="pwm-card border-slate-700 space-y-3">
          <div className="text-sm">
            <span className="text-pwm-muted">Filter by physics:</span>
            {(params.carrier || params.problem_class || params.noise_model) && (
              <Link href={buildHref({ carrier: undefined, problem_class: undefined, noise_model: undefined })}
                    className="ml-3 pwm-link text-xs">clear all facets</Link>
            )}
          </div>
          {topFacets('carrier').length > 0 && (
            <div className="flex flex-wrap items-baseline gap-2 text-xs">
              <span className="text-pwm-muted w-24 shrink-0">Carrier</span>
              {topFacets('carrier').map(([v, n]) => facetPill('carrier', v, n))}
            </div>
          )}
          {topFacets('problem_class').length > 0 && (
            <div className="flex flex-wrap items-baseline gap-2 text-xs">
              <span className="text-pwm-muted w-24 shrink-0">Problem class</span>
              {topFacets('problem_class').map(([v, n]) => facetPill('problem_class', v, n))}
            </div>
          )}
          {topFacets('noise_model').length > 0 && (
            <div className="flex flex-wrap items-baseline gap-2 text-xs">
              <span className="text-pwm-muted w-24 shrink-0">Noise model</span>
              {topFacets('noise_model').map(([v, n]) => facetPill('noise_model', v, n))}
            </div>
          )}
          <p className="text-xs text-pwm-muted italic">
            Photon, electron, mechanical, etc. drawn from each manifest&apos;s
            <code className="px-1">physics_fingerprint</code> block. Combine multiple facets to narrow further.
          </p>
        </div>
      )}

      {data.domains.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <span className="pwm-pill text-pwm-muted !border-transparent">Domain:</span>
          <Link
            href={buildHref({ domain: undefined })}
            className={`pwm-pill ${!domainFilter ? '!text-white !border-pwm-accent' : ''}`}
          >
            All
          </Link>
          {data.domains.map((d) => (
            <Link
              key={d}
              href={buildHref({ domain: d })}
              className={`pwm-pill ${domainFilter === d ? '!text-white !border-pwm-accent' : ''}`}
            >
              {d}
            </Link>
          ))}
        </div>
      )}

      {filtered.length === 0 ? (
        <Empty>
          {q || domainFilter
            ? <>No principles match those filters. <Link href={`/principles?tier=${tier}`} className="pwm-link">Clear filters</Link>.</>
            : tier === 'stub'
              ? <>No stub principles found in the catalog tree.</>
              : <>No genesis principles yet. As content agents publish L1 JSONs under{' '}<code>pwm_product/genesis/l1/</code>, they&apos;ll appear here.</>}
        </Empty>
      ) : (
        <div className="pwm-card overflow-x-auto">
          <table className="pwm-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>ID</th>
                <th>Domain</th>
                <th>Tier</th>
                <th>δ</th>
                <th>L_DAG</th>
                <th>Specs</th>
                <th>Benchmarks</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => {
                const isStub = (p.registration_tier ?? 'stub') === 'stub';
                return (
                  <tr key={p.artifact_id} className={`hover:bg-slate-900/50 ${isStub ? 'opacity-60' : ''}`}>
                    <td>
                      <Link className="pwm-link" href={`/principles/${p.artifact_id}`}>
                        {p.title}
                      </Link>
                    </td>
                    <td className="font-mono text-pwm-muted text-xs">
                      {p.artifact_id}
                    </td>
                    <td>
                      <span className="pwm-pill">{p.domain}</span>
                    </td>
                    <td>{tierBadge(p.registration_tier)}</td>
                    <td>{p.difficulty_delta ?? '—'}</td>
                    <td>{p.L_DAG ?? '—'}</td>
                    <td>{p.active_spec_count ?? 0}</td>
                    <td>{p.active_benchmark_count ?? 0}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
