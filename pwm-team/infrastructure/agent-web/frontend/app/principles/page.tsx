import Link from 'next/link';
import { api } from '@/lib/api';
import { ApiDown, Empty } from '@/components/Empty';

export default async function PrinciplesPage({
  searchParams,
}: {
  searchParams: Promise<{ domain?: string }>;
}) {
  const data = await api.principles();
  const params = await searchParams;
  if (!data) return <ApiDown />;

  const filtered = params.domain
    ? data.genesis.filter((p) => p.domain === params.domain)
    : data.genesis;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-3xl font-bold tracking-tight">Principles</h1>
        <div className="text-sm text-pwm-muted">
          {filtered.length} of {data.genesis.length} shown
        </div>
      </div>

      {data.domains.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <Link
            href="/principles"
            className={`pwm-pill ${!params.domain ? '!text-white !border-pwm-accent' : ''}`}
          >
            All
          </Link>
          {data.domains.map((d) => (
            <Link
              key={d}
              href={`/principles?domain=${encodeURIComponent(d)}`}
              className={`pwm-pill ${params.domain === d ? '!text-white !border-pwm-accent' : ''}`}
            >
              {d}
            </Link>
          ))}
        </div>
      )}

      {filtered.length === 0 ? (
        <Empty>
          No genesis principles match. As content agents publish L1 JSONs under{' '}
          <code>pwm_product/genesis/l1/</code>, they&apos;ll appear here.
        </Empty>
      ) : (
        <div className="pwm-card overflow-x-auto">
          <table className="pwm-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
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
                  <td className="font-mono">
                    <Link className="pwm-link" href={`/principles/${p.artifact_id}`}>
                      {p.artifact_id}
                    </Link>
                  </td>
                  <td>{p.title}</td>
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
