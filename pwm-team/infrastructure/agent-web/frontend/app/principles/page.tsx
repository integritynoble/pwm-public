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
  searchParams: Promise<{ domain?: string; q?: string; tier?: string }>;
}) {
  const params = await searchParams;
  const tier: Tier = isTier(params.tier);
  const data = await api.principles(tier);
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

  const tierTab = (label: string, value: Tier, count: number) => {
    const qs = new URLSearchParams();
    qs.set('tier', value);
    if (domainFilter) qs.set('domain', domainFilter);
    if (q) qs.set('q', q);
    const active = tier === value;
    return (
      <Link
        href={`/principles?${qs.toString()}`}
        className={`pwm-pill ${active ? '!text-white !border-pwm-accent' : ''}`}
      >
        {label} <span className="text-pwm-muted">({count})</span>
      </Link>
    );
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

      {data.domains.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <Link
            href={`/principles?tier=${tier}${q ? `&q=${encodeURIComponent(q)}` : ''}`}
            className={`pwm-pill ${!domainFilter ? '!text-white !border-pwm-accent' : ''}`}
          >
            All
          </Link>
          {data.domains.map((d) => {
            const qs = new URLSearchParams();
            qs.set('tier', tier);
            qs.set('domain', d);
            if (q) qs.set('q', q);
            return (
              <Link
                key={d}
                href={`/principles?${qs.toString()}`}
                className={`pwm-pill ${domainFilter === d ? '!text-white !border-pwm-accent' : ''}`}
              >
                {d}
              </Link>
            );
          })}
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
