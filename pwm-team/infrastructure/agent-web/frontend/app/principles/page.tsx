import Link from 'next/link';
import { api } from '@/lib/api';
import { ApiDown, Empty } from '@/components/Empty';

export default async function PrinciplesPage({
  searchParams,
}: {
  searchParams: Promise<{ domain?: string; q?: string }>;
}) {
  const data = await api.principles();
  const params = await searchParams;
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-3xl font-bold tracking-tight">Principles</h1>
        <div className="text-sm text-pwm-muted">
          {filtered.length} of {data.genesis.length} shown
        </div>
      </div>

      <form action="/principles" method="GET" className="flex gap-2">
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
            href={q ? `/principles?q=${encodeURIComponent(q)}` : '/principles'}
            className={`pwm-pill ${!domainFilter ? '!text-white !border-pwm-accent' : ''}`}
          >
            All
          </Link>
          {data.domains.map((d) => {
            const qs = new URLSearchParams();
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
            ? <>No principles match those filters. <Link href="/principles" className="pwm-link">Clear filters</Link>.</>
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
                <th>δ</th>
                <th>L_DAG</th>
                <th>Specs</th>
                <th>Benchmarks</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.artifact_id} className="hover:bg-slate-900/50">
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
                  <td>{p.difficulty_delta ?? '—'}</td>
                  <td>{p.L_DAG ?? '—'}</td>
                  <td>{p.active_spec_count ?? 0}</td>
                  <td>{p.active_benchmark_count ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
