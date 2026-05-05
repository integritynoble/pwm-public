import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { api, type Demo } from '@/lib/api';
import { shortAddr, weiToPwm } from '@/lib/format';
import { StatusBadge } from '@/components/Badges';

const PUBLIC_REPO = 'https://github.com/integritynoble/pwm-public/blob/main';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ ref: string }>;
}): Promise<Metadata> {
  const { ref } = await params;
  const data = await api.benchmark(ref);
  const title = data?.genesis?.title
    ? `${data.genesis.title} · PWM benchmark`
    : `Benchmark ${ref.slice(0, 10)}… · PWM`;
  return { title };
}

export default async function BenchmarkDetail({ params }: { params: Promise<{ ref: string }> }) {
  const { ref } = await params;
  const [data, lb] = await Promise.all([
    api.benchmark(ref),
    api.leaderboard(ref).catch(() => null),  // tolerate API miss; header degrades gracefully
  ]);
  if (!data) return notFound();

  const g = data.genesis;
  const chain = data.chain;
  const tier = g?.ibenchmark_range?.center_ibenchmark ?? {};
  const bounds = g?.ibenchmark_range?.tier_bounds ?? {};
  const baselines = g?.protocol_fields?.baselines ?? [];

  const chainHashForLeaderboard = chain?.hash;

  return (
    <div className="space-y-8">
      <div>
        <Link href="/benchmarks" className="pwm-link text-sm">← All benchmarks</Link>
        <h1 className="text-3xl font-bold tracking-tight mt-2">
          {g?.title ?? ref}
          <span className="text-pwm-muted text-lg ml-3">{g?.artifact_id ?? shortAddr(ref)}</span>
        </h1>
        {(ref === 'L3-003' || ref === 'L3-004') && (
          <Link
            href={`/walkthroughs/${ref === 'L3-003' ? 'cassi' : 'cacti'}`}
            className="inline-block mt-4 px-4 py-2 rounded bg-gradient-to-r from-cyan-500 to-indigo-500 text-black font-semibold text-sm"
          >
            Read full 4-layer walkthrough →
          </Link>
        )}
      </div>

      <section className="grid md:grid-cols-2 gap-4">
        <div className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">Genesis spec</h2>
          {g ? (
            <dl className="text-sm space-y-1">
              <div><dt className="inline text-pwm-muted">Parent L2:</dt> <dd className="inline ml-2 font-mono">{g.parent_l2 ?? '—'}</dd></div>
              <div><dt className="inline text-pwm-muted">Spec type:</dt> <dd className="inline ml-2">{g.spec_type ?? '—'}</dd></div>
              <div><dt className="inline text-pwm-muted">d_spec:</dt> <dd className="inline ml-2">{g.d_spec ?? '—'}</dd></div>
              {tier.rho != null && <div><dt className="inline text-pwm-muted">ρ:</dt> <dd className="inline ml-2">{tier.rho}</dd></div>}
              {tier.epsilon != null && <div><dt className="inline text-pwm-muted">ε:</dt> <dd className="inline ml-2">{tier.epsilon}</dd></div>}
            </dl>
          ) : (
            <p className="text-pwm-muted italic text-sm">No off-chain spec linked.</p>
          )}
        </div>

        <div className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">On-chain</h2>
          {chain ? (
            <dl className="text-sm space-y-1">
              <div><dt className="inline text-pwm-muted">Hash:</dt> <dd className="inline ml-2 font-mono break-all">{chain.hash}</dd></div>
              <div><dt className="inline text-pwm-muted">Creator:</dt> <dd className="inline ml-2 font-mono">{shortAddr(chain.creator)}</dd></div>
              <div><dt className="inline text-pwm-muted">Block:</dt> <dd className="inline ml-2">{chain.block_number}</dd></div>
              <div><dt className="inline text-pwm-muted">Pool:</dt> <dd className="inline ml-2">{weiToPwm(data.pool_balance_wei)} PWM</dd></div>
            </dl>
          ) : (
            <p className="text-pwm-muted italic text-sm">Not registered on-chain yet.</p>
          )}
        </div>
      </section>

      {Object.keys(tier).length > 0 && (
        <section className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">Ω tier</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            {Object.entries(tier.omega_tier ?? {}).map(([k, v]) => (
              <div key={k} className="bg-slate-950/60 border border-slate-800 rounded px-2 py-1">
                <div className="text-xs text-pwm-muted">{k}</div>
                <div className="font-mono">{String(v)}</div>
                {bounds[k] && (
                  <div className="text-[10px] text-slate-500 font-mono">∈ [{bounds[k][0]}, {bounds[k][1]}]</div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {baselines.length > 0 && (
        <section className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">Baselines</h2>
          <table className="pwm-table">
            <thead>
              <tr><th>Name</th><th>Method</th><th>Expected PSNR</th></tr>
            </thead>
            <tbody>
              {baselines.map((b: any) => (
                <tr key={b.name}>
                  <td>{b.name}</td>
                  <td className="font-mono text-xs">{b.method_sig}</td>
                  <td>{b.expected_psnr} dB</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {lb && <SotaReferenceDeltaHeader lb={lb} />}

      {data.demo && <ExampleDataSection demo={data.demo} />}

      {data.demo && <GetThisBenchmarkSection demo={data.demo} benchmarkRef={ref} />}

      <section>
        <div className="flex items-baseline justify-between mb-3">
          <h2 className="text-lg font-semibold">Leaderboard (top 10)</h2>
          {chainHashForLeaderboard && (
            <Link href={`/leaderboard/${chainHashForLeaderboard}`} className="pwm-link text-sm">
              Full leaderboard →
            </Link>
          )}
        </div>
        {data.leaderboard.length === 0 ? (
          <div className="pwm-card text-pwm-muted italic">
            No solutions submitted yet. The reference baseline above is the floor — submit a better solver to claim rank 1.
          </div>
        ) : (
          <div className="pwm-card overflow-x-auto">
            <table className="pwm-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Cert</th>
                  <th>Solver</th>
                  <th>PSNR</th>
                  <th>Submitter</th>
                  <th>Q</th>
                  <th>Status</th>
                  <th>Draw</th>
                </tr>
              </thead>
              <tbody>
                {data.leaderboard.map((c: any, i: number) => (
                  <tr key={c.cert_hash}>
                    <td>{rankBadge(c.draw_rank ?? i + 1)}</td>
                    <td className="font-mono">
                      <Link className="pwm-link" href={`/cert/${c.cert_hash}`}>{shortAddr(c.cert_hash)}</Link>
                    </td>
                    <td>
                      {c.solver_label ?? <span className="text-pwm-muted italic">—</span>}
                    </td>
                    <td className="font-mono">
                      {c.psnr_db != null
                        ? `${Number(c.psnr_db).toFixed(1)} dB`
                        : <span className="text-pwm-muted italic">—</span>}
                    </td>
                    <td className="font-mono">{shortAddr(c.submitter)}</td>
                    <td>{c.q_int}</td>
                    <td><StatusBadge status={c.status} /></td>
                    <td>{c.draw_amount ? `${weiToPwm(c.draw_amount)} PWM` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}


/** Visual rank badge: gold/silver/bronze for top 3, ribbon for 4-10, plain # for 11+. */
function rankBadge(rank: number | null | undefined): string {
  if (rank == null) return '#?';
  if (rank === 1) return '🥇 #1';
  if (rank === 2) return '🥈 #2';
  if (rank === 3) return '🥉 #3';
  if (rank <= 10) return `🎗 #${rank}`;
  return `#${rank}`;
}


/**
 * SOTA / Reference / Delta header — the protocol storytelling block.
 *
 * Shows three things side-by-side:
 *   - Current SOTA (best on-chain cert) — dynamic
 *   - Reference floor (off-chain GAP-TV-class baseline) — static
 *   - Improvement delta — the protocol's value proposition in one number
 *
 * Empty-leaderboard fallback: if no certs exist, shows just the
 * reference floor with a "be the first to submit" call-to-action.
 */
function SotaReferenceDeltaHeader({ lb }: { lb: NonNullable<Awaited<ReturnType<typeof api.leaderboard>>> }) {
  const sota = lb.current_sota;
  const ref = lb.reference;
  const refAdvanced = (lb as any).reference_advanced as
    | { label?: string | null; psnr_db?: number | null; tier?: string | null }
    | null
    | undefined;
  const delta = lb.improvement_db;

  // Don't render the section at all if neither side has data.
  if (!sota && !ref) return null;

  return (
    <section className="pwm-card border-cyan-500/30 space-y-3">
      <h2 className="text-lg font-semibold">Current standing</h2>
      <div className="grid md:grid-cols-3 gap-3 text-sm">
        {/* SOTA */}
        <div className="bg-slate-950/60 border border-cyan-500/40 rounded px-3 py-3">
          <div className="text-xs uppercase tracking-wide text-cyan-400 mb-1">🏆 Current SOTA</div>
          {sota ? (
            <>
              <div className="font-semibold">
                {sota.solver_label ?? <span className="text-pwm-muted italic">unlabeled</span>}
              </div>
              <div className="font-mono text-lg">
                {sota.psnr_db != null ? `${Number(sota.psnr_db).toFixed(2)} dB` : '—'}
              </div>
              <div className="text-xs text-pwm-muted mt-1">
                {rankBadge(sota.rank)} · cert{' '}
                <Link className="pwm-link font-mono" href={`/cert/${sota.cert_hash}`}>
                  {shortAddr(sota.cert_hash)}
                </Link>
              </div>
            </>
          ) : (
            <>
              <div className="text-pwm-muted italic text-sm">No certs submitted yet.</div>
              <div className="text-xs text-pwm-muted mt-2">
                Be the first to submit a solution and claim rank 1.
              </div>
            </>
          )}
        </div>

        {/* Reference (classical + optional deep-learning floor stacked) */}
        <div className="bg-slate-950/60 border border-slate-700 rounded px-3 py-3 space-y-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-slate-400 mb-1">📊 Classical floor</div>
            {ref ? (
              <>
                <div className="font-semibold">
                  {ref.label ?? <span className="text-pwm-muted italic">unnamed</span>}
                </div>
                <div className="font-mono text-lg">
                  {ref.psnr_db != null ? `${Number(ref.psnr_db).toFixed(2)} dB` : '—'}
                </div>
                <div className="text-xs text-pwm-muted mt-1">
                  deliberate floor; anyone better wins
                </div>
              </>
            ) : (
              <div className="text-pwm-muted italic text-sm">No reference baseline declared.</div>
            )}
          </div>
          {refAdvanced && (
            <div className="border-t border-slate-700 pt-3">
              <div className="text-xs uppercase tracking-wide text-fuchsia-400 mb-1">🧠 Deep-learning floor</div>
              <div className="font-semibold">
                {refAdvanced.label ?? <span className="text-pwm-muted italic">unnamed</span>}
              </div>
              <div className="font-mono text-lg">
                {refAdvanced.psnr_db != null ? `${Number(refAdvanced.psnr_db).toFixed(2)} dB` : '—'}
              </div>
              <div className="text-xs text-pwm-muted mt-1">
                published deep-learning landmark; harder gate
              </div>
            </div>
          )}
        </div>

        {/* Delta */}
        <div className="bg-slate-950/60 border border-emerald-500/40 rounded px-3 py-3">
          <div className="text-xs uppercase tracking-wide text-emerald-400 mb-1">📈 PWM-enabled delta</div>
          {delta != null ? (
            <>
              <div className="font-mono text-lg">
                {delta >= 0 ? '+' : ''}
                {delta.toFixed(2)} dB
              </div>
              <div className="text-xs text-pwm-muted mt-1">
                {delta > 0
                  ? 'community submission improved on the floor'
                  : 'no improvement yet'}
              </div>
            </>
          ) : (
            <div className="text-pwm-muted italic text-sm">
              Delta unavailable (need both SOTA and reference PSNR).
            </div>
          )}
        </div>
      </div>
    </section>
  );
}


function fmtBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}


function PreviewTile({
  label,
  src,
  alt,
  shape,
  badge,
}: {
  label: string;
  src: string;
  alt: string;
  shape?: number[];
  badge?: string;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <div className="text-xs text-pwm-muted">{label}</div>
        {badge && (
          <span className="text-[10px] font-semibold text-emerald-400">{badge}</span>
        )}
      </div>
      <img
        src={src}
        alt={alt}
        className="w-full border border-slate-800 rounded bg-slate-950 [image-rendering:pixelated]"
        loading="lazy"
      />
      {shape && (
        <div className="text-[10px] text-slate-500 font-mono mt-1">
          shape {JSON.stringify(shape)}
        </div>
      )}
    </div>
  );
}


function ExampleDataSection({ demo }: { demo: Demo }) {
  const samples = demo.samples.slice(0, 2); // show first 2 samples
  return (
    <section>
      <h2 className="text-lg font-semibold mb-3">Example data</h2>
      <p className="text-sm text-pwm-muted mb-4 max-w-3xl">
        Two independent samples from the InverseNet benchmark, each shown as
        <strong> measurement → ground truth → reference reconstruction</strong>.
        The reconstruction is the reference solver&apos;s output — the bar a
        competing solver must beat to win the bounty.
      </p>
      <div className="space-y-4">
        {samples.map((s) => {
          const sceneId = (s.meta as any).scene_id;
          const psnr = s.meta.reference_solver_psnr_db;
          return (
            <div key={s.name} className="pwm-card space-y-3">
              <div className="flex items-baseline justify-between flex-wrap gap-2">
                <h3 className="font-mono text-sm font-semibold">
                  {s.name}{sceneId ? ` · ${sceneId}` : ''}
                </h3>
                <span className="text-xs text-pwm-muted">
                  reference PSNR {psnr} dB
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <PreviewTile
                  label="Measurement"
                  src={`/api/demos/${demo.name}/${s.name}/snapshot.png`}
                  alt={`${demo.name} ${s.name} measurement`}
                  shape={s.meta.shape_snapshot}
                />
                <PreviewTile
                  label="Ground truth"
                  src={`/api/demos/${demo.name}/${s.name}/ground_truth.png`}
                  alt={`${demo.name} ${s.name} ground truth`}
                  shape={s.meta.shape_ground_truth}
                />
                <PreviewTile
                  label="Reference reconstruction"
                  src={`/api/demos/${demo.name}/${s.name}/solution.png`}
                  alt={`${demo.name} ${s.name} reconstruction`}
                  shape={s.meta.shape_solution}
                  badge={psnr ? `${psnr} dB` : undefined}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}


function GetThisBenchmarkSection({
  demo,
  benchmarkRef,
}: {
  demo: Demo;
  benchmarkRef: string;
}) {
  const first = demo.samples[0];
  const solverPath = first?.meta.reference_solver;
  const cardYamlPath = `pwm-team/pwm_product/benchmark_cards/${demo.benchmark_id}.yaml`;
  const l3JsonPath = `pwm-team/pwm_product/genesis/l3/${demo.benchmark_id}.json`;
  const bountyIndexPath = 'pwm-team/bounties/INDEX.md';
  const demosReadmePath = `pwm-team/pwm_product/demos/${demo.name}/README.md`;

  return (
    <section className="pwm-card space-y-4 border-cyan-500/30">
      <div>
        <h2 className="text-lg font-semibold">Get this benchmark</h2>
        <p className="text-sm text-pwm-muted mt-1 max-w-3xl">
          Everything you need to run the reference solver locally, browse
          the full benchmark specification, or submit a competing solution.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-3 text-sm">
        <div>
          <h3 className="text-xs uppercase tracking-wide text-pwm-muted mb-2">
            Download sample data
          </h3>
          <div className="space-y-1">
            {demo.samples.map((s) => (
              <details key={s.name} className="bg-slate-950/60 border border-slate-800 rounded px-3 py-2">
                <summary className="cursor-pointer font-mono text-xs">
                  {s.name} · {Object.values(s.files).reduce((a, b) => a + b, 0)} B
                </summary>
                <ul className="mt-2 space-y-1 text-xs">
                  {Object.entries(s.files).map(([name, size]) => (
                    <li key={name} className="flex justify-between">
                      <a
                        className="pwm-link font-mono"
                        href={`/api/demos/${demo.name}/${s.name}/${name}`}
                        download
                      >
                        {name}
                      </a>
                      <span className="text-slate-500">{fmtBytes(size)}</span>
                    </li>
                  ))}
                </ul>
              </details>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-xs uppercase tracking-wide text-pwm-muted mb-2">
            Browse on GitHub
          </h3>
          <ul className="space-y-1 text-sm">
            <li>
              <a className="pwm-link" href={`${PUBLIC_REPO}/${cardYamlPath}`} target="_blank" rel="noreferrer">
                Benchmark card
              </a>{' '}
              <span className="text-xs text-pwm-muted">(YAML spec)</span>
            </li>
            <li>
              <a className="pwm-link" href={`${PUBLIC_REPO}/${l3JsonPath}`} target="_blank" rel="noreferrer">
                L3 principle JSON
              </a>{' '}
              <span className="text-xs text-pwm-muted">(canonical on-chain spec)</span>
            </li>
            {solverPath && (
              <li>
                <a className="pwm-link" href={`${PUBLIC_REPO}/${solverPath}`} target="_blank" rel="noreferrer">
                  Reference solver
                </a>{' '}
                <span className="text-xs text-pwm-muted">(Python)</span>
              </li>
            )}
            <li>
              <a className="pwm-link" href={`${PUBLIC_REPO}/${demosReadmePath}`} target="_blank" rel="noreferrer">
                Demo README
              </a>{' '}
              <span className="text-xs text-pwm-muted">(full pipeline walkthrough)</span>
            </li>
            <li>
              <a className="pwm-link" href={`${PUBLIC_REPO}/${bountyIndexPath}`} target="_blank" rel="noreferrer">
                Bounty index
              </a>{' '}
              <span className="text-xs text-pwm-muted">(compete with a better solver)</span>
            </li>
          </ul>
        </div>
      </div>

      {first?.meta.how_to_run && (
        <div>
          <h3 className="text-xs uppercase tracking-wide text-pwm-muted mb-2">
            Run the reference solver locally
          </h3>
          <pre className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs overflow-x-auto">
{`git clone https://github.com/integritynoble/pwm-public.git
cd pwm-public
${first.meta.how_to_run}
cat /tmp/out/meta.json`}
          </pre>
          <p className="text-xs text-pwm-muted mt-2">
            Expected reference PSNR: {first.meta.reference_solver_psnr_db} dB (seed{' '}
            {first.meta.seed}). Byte-stable across runs at the same git SHA.
          </p>
        </div>
      )}
    </section>
  );
}
