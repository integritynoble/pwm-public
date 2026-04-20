import Link from 'next/link';
import { notFound } from 'next/navigation';
import { api } from '@/lib/api';
import { ForwardModel } from '@/components/Math';
import { weiToPwm } from '@/lib/format';

export default async function PrincipleDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const data = await api.principle(id);
  if (!data) return notFound();
  const p = data.principle;
  const e = p.E ?? {};
  const g = p.G ?? {};
  const w = p.W ?? {};
  const c = p.C ?? {};

  return (
    <div className="space-y-8">
      <div>
        <Link href="/principles" className="pwm-link text-sm">← All principles</Link>
        <h1 className="text-3xl font-bold tracking-tight mt-2">
          {p.title} <span className="text-pwm-muted text-lg">{p.artifact_id}</span>
        </h1>
        <div className="mt-2 flex flex-wrap gap-2 text-sm">
          <span className="pwm-pill">{p.domain}</span>
          {p.sub_domain && <span className="pwm-pill">{p.sub_domain}</span>}
          {p.difficulty_tier && <span className="pwm-pill">δ={p.difficulty_delta} · {p.difficulty_tier}</span>}
          {g.L_DAG != null && <span className="pwm-pill">L_DAG = {g.L_DAG}</span>}
        </div>
      </div>

      <section className="pwm-card">
        <h2 className="text-lg font-semibold mb-2">Forward model E</h2>
        <ForwardModel text={e.forward_model} />
        {e.description && <p className="text-sm text-pwm-muted mt-3">{e.description}</p>}
      </section>

      {g.dag && (
        <section className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">L-DAG</h2>
          <div className="font-mono text-sm whitespace-pre-wrap bg-slate-950/60 p-3 rounded border border-slate-800">
            {g.dag}
          </div>
          {Array.isArray(g.vertices) && (
            <div className="mt-3 flex flex-wrap gap-2">
              {g.vertices.map((v: string) => (
                <span key={v} className="pwm-pill">{v}</span>
              ))}
            </div>
          )}
        </section>
      )}

      <section className="grid md:grid-cols-2 gap-4">
        <div className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">Well-posedness W</h2>
          <dl className="text-sm space-y-1">
            <div><dt className="inline text-pwm-muted">Existence:</dt> <dd className="inline ml-2">{String(w.existence ?? '—')}</dd></div>
            <div><dt className="inline text-pwm-muted">Uniqueness:</dt> <dd className="inline ml-2">{String(w.uniqueness ?? '—')}</dd></div>
            <div><dt className="inline text-pwm-muted">Stability:</dt> <dd className="inline ml-2">{w.stability ?? '—'}</dd></div>
            <div><dt className="inline text-pwm-muted">κ:</dt> <dd className="inline ml-2">{w.condition_number_kappa ?? '—'}</dd></div>
          </dl>
          {w.regime && <p className="text-sm text-pwm-muted mt-3 italic">{w.regime}</p>}
        </div>
        <div className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">Solvability C</h2>
          <dl className="text-sm space-y-1">
            <div><dt className="inline text-pwm-muted">Solver class:</dt> <dd className="inline ml-2">{c.solver_class ?? '—'}</dd></div>
            <div><dt className="inline text-pwm-muted">Convergence rate q:</dt> <dd className="inline ml-2">{c.convergence_rate_q ?? '—'}</dd></div>
            <div><dt className="inline text-pwm-muted">Complexity:</dt> <dd className="inline ml-2 font-mono text-xs">{c.complexity ?? '—'}</dd></div>
          </dl>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Specs ({data.specs.length})</h2>
        {data.specs.length === 0 ? (
          <div className="pwm-card text-pwm-muted italic">No L2 specs registered yet for this principle.</div>
        ) : (
          <div className="pwm-card overflow-x-auto">
            <table className="pwm-table">
              <thead>
                <tr><th>Spec ID</th><th>Title</th><th>Type</th><th>d_spec</th></tr>
              </thead>
              <tbody>
                {data.specs.map((s) => (
                  <tr key={s.artifact_id}>
                    <td className="font-mono">{s.artifact_id}</td>
                    <td>{s.title}</td>
                    <td>{s.spec_type}</td>
                    <td>{s.d_spec ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="grid md:grid-cols-2 gap-4">
        <div className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">Treasury (T_k)</h2>
          <p className="text-sm">
            Balance: <span className="font-mono">{weiToPwm(data.treasury_balance_wei)} PWM</span>
          </p>
        </div>
        <div className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">Minting</h2>
          <p className="text-sm">
            Total minted: <span className="font-mono">{weiToPwm(data.total_minted_wei)} PWM</span>
          </p>
          {data.chain_meta?.delta && (
            <p className="text-sm mt-1">
              On-chain δ: <span className="font-mono">{data.chain_meta.delta}</span>
              {data.chain_meta.promoted === 1 && (
                <span className="pwm-pill ml-2 !text-emerald-300">promoted</span>
              )}
            </p>
          )}
        </div>
      </section>

      {data.registered_benchmarks?.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Registered benchmarks (on-chain)</h2>
          <div className="pwm-card overflow-x-auto">
            <table className="pwm-table">
              <thead>
                <tr><th>Hash</th><th>ρ</th><th>Registered</th></tr>
              </thead>
              <tbody>
                {data.registered_benchmarks.map((b) => (
                  <tr key={b.benchmark_hash}>
                    <td className="font-mono">
                      <a className="pwm-link" href={`/benchmarks/${b.benchmark_hash}`}>
                        {b.benchmark_hash.slice(0, 10)}…{b.benchmark_hash.slice(-6)}
                      </a>
                    </td>
                    <td>{b.rho}</td>
                    <td className="text-xs text-pwm-muted">
                      {new Date(b.registered_at * 1000).toISOString().split('T')[0]}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
