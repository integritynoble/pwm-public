import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { api } from '@/lib/api';
import { ForwardModel } from '@/components/Math';
import { weiToPwm } from '@/lib/format';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const data = await api.principle(id);
  if (!data) return { title: `${id} not found · PWM Explorer` };
  const title = `${data.principle.title} (${data.principle.artifact_id}) · PWM`;
  const description: string = data.principle?.E?.description?.slice(0, 200) ?? `PWM principle ${id}`;
  return { title, description };
}

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
  const isStub = data.is_stub === true || (p.registration_tier ?? 'stub') === 'stub';
  const tier = (p.registration_tier ?? 'stub') as string;
  const walkthroughAnchor: string | null =
    id === 'L1-003' ? 'cassi' : id === 'L1-004' ? 'cacti' : null;

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
          {tier === 'founder_vetted' && (
            <span className="pwm-pill !text-emerald-300 !border-emerald-500/40">★ Founder-vetted</span>
          )}
          {tier === 'community_proposed' && (
            <span className="pwm-pill !text-cyan-300 !border-cyan-500/40">✓ Community-vetted</span>
          )}
          {tier === 'stub' && (
            <span className="pwm-pill !text-slate-400 !border-slate-600">📋 Stub — not mineable</span>
          )}
        </div>
        {walkthroughAnchor && !isStub && (
          <Link
            href={`/walkthroughs/${walkthroughAnchor}`}
            className="inline-block mt-4 px-4 py-2 rounded bg-gradient-to-r from-cyan-500 to-indigo-500 text-black font-semibold text-sm"
          >
            Read full 4-layer walkthrough →
          </Link>
        )}
        {isStub && (
          <div className="mt-4 pwm-card !border-amber-700/40 !bg-amber-950/10">
            <div className="flex items-start gap-3">
              <span className="text-2xl">📋</span>
              <div className="flex-1">
                <h3 className="text-amber-200 font-semibold mb-1">Unclaimed Principle — open for contribution</h3>
                <p className="text-sm text-amber-100/70 mb-3">
                  This Principle is declared in the catalog but has no reference solver, no pinned dataset,
                  and is not registered on-chain. There is no reward pool. Submitting a cert against this
                  Principle today will record the cert for reproducibility but pay zero PWM.
                </p>
                <p className="text-sm text-amber-100/70 mb-3">
                  <strong className="text-amber-200">To claim it</strong> as a Bounty #7 contribution:
                  open a PR adding (1) a reference solver, (2) ≥1 dataset pinned to IPFS, (3) updates to
                  the L3 manifest with dataset CIDs. After verifier-agent triple-review, the founders&apos;
                  3-of-5 multisig signs <code>PWMRegistry.register()</code> and the Principle becomes mineable.
                </p>
                <div className="flex flex-wrap gap-3 text-sm">
                  <a
                    href="https://github.com/integritynoble/pwm-public/blob/main/pwm-team/customer_guide/PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block px-4 py-2 rounded bg-amber-600/80 hover:bg-amber-500 text-black font-semibold"
                  >
                    Read the contribution guide →
                  </a>
                  <a
                    href={`https://github.com/integritynoble/pwm-public/issues/new?title=%5B${p.artifact_id}+claim%5D+${encodeURIComponent(p.title || '')}&body=I+want+to+claim+${p.artifact_id}+(${encodeURIComponent(p.title || '')}).%0A%0A**Reference+solver:**+%3CdescribeYourSolverApproach%3E%0A%0A**Dataset:**+%3CdescribeYourDataset%3E%0A%0A**Estimated+timeline:**+%3CweeksFromMerge%3E`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block px-4 py-2 rounded border border-amber-500/40 text-amber-200 hover:bg-amber-900/20 font-semibold"
                  >
                    Open a claim issue →
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}
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
                    <td className="font-mono">
                      <Link className="pwm-link" href={`/specs/${s.artifact_id}`}>
                        {s.artifact_id}
                      </Link>
                    </td>
                    <td>
                      <Link className="pwm-link" href={`/specs/${s.artifact_id}`}>
                        {s.title}
                      </Link>
                    </td>
                    <td>{s.spec_type}</td>
                    <td>{s.d_spec ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {!isStub && (
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
      )}

      {!isStub && data.registered_benchmarks?.length > 0 && (
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
