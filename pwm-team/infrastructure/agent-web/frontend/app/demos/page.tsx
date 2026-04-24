import Link from 'next/link';
import { api } from '@/lib/api';
import { ApiDown } from '@/components/Empty';

export const dynamic = 'force-dynamic';

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}

export default async function DemosPage() {
  const data = await api.demos();
  if (!data) return <ApiDown />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Demos</h1>
        <p className="text-sm text-pwm-muted mt-2 max-w-2xl">
          Canonical demo datasets — committed to the repo, small
          (&lt; 50 KB each), deterministic. Each benchmark ships two
          independent samples so solver output isn&apos;t cherry-picked.
          Download the input, run the reference solver locally, and see
          the PWM pipeline work in under a minute. <strong>These are not
          the real benchmarks.</strong> They exist so newcomers can verify
          the pipeline end-to-end before burning gas on a real{' '}
          <Link href="/bounties" className="pwm-link">mine</Link>.
        </p>
      </div>

      {data.demos.length === 0 && (
        <div className="pwm-card">
          <div className="text-sm text-pwm-muted">
            No demos available. Run{' '}
            <code className="text-slate-400">python3 scripts/generate_demos.py</code>{' '}
            from the repo root to populate{' '}
            <code className="text-slate-400">pwm-team/pwm_product/demos/</code>.
          </div>
        </div>
      )}

      {data.demos.map((d) => {
        const first = d.samples[0];
        return (
          <div key={d.name} className="pwm-card space-y-4">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <div className="text-xs text-pwm-muted uppercase tracking-wide">
                  {first?.meta.tier_approx ?? ''}
                </div>
                <h2 className="text-xl font-semibold mt-1 font-mono">
                  {d.name}
                </h2>
                <p className="text-sm text-pwm-muted mt-1">
                  {first?.meta.benchmark}
                </p>
                {d.benchmark_id && (
                  <Link
                    href={`/benchmarks/${d.benchmark_id}`}
                    className="pwm-link text-sm"
                  >
                    Full benchmark page → {d.benchmark_id}
                  </Link>
                )}
              </div>
              {first?.meta.reference_solver_psnr_db !== undefined && (
                <div className="text-right text-sm">
                  <div className="text-xs text-pwm-muted">reference PSNR</div>
                  <div className="text-xl font-semibold text-pwm-accent">
                    {first.meta.reference_solver_psnr_db.toFixed(1)} dB
                  </div>
                  <div className="text-xs text-pwm-muted mt-0.5">
                    your solver should beat this
                  </div>
                </div>
              )}
            </div>

            <div>
              <div className="text-xs uppercase tracking-wide text-pwm-muted mb-1">
                Shape summary
              </div>
              <div className="text-sm space-y-0.5 font-mono">
                {first?.meta.shape_snapshot && (
                  <div>snapshot: [{first.meta.shape_snapshot.join(', ')}]</div>
                )}
                {first?.meta.shape_ground_truth && (
                  <div>ground truth: [{first.meta.shape_ground_truth.join(', ')}]</div>
                )}
                {first?.meta.shape_solution && (
                  <div>reference solution: [{first.meta.shape_solution.join(', ')}]</div>
                )}
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-3">
              {d.samples.map((s) => (
                <div key={s.name} className="border border-slate-800 rounded p-3 bg-slate-950/40 space-y-2">
                  <div className="flex items-baseline justify-between">
                    <div className="font-mono text-sm font-semibold">{s.name}</div>
                    <div className="text-xs text-pwm-muted">
                      seed {s.meta.seed} · {s.meta.reference_solver_psnr_db} dB
                    </div>
                  </div>
                  {(s.files['snapshot.png'] || s.files['ground_truth.png']) && (
                    <div className="grid grid-cols-2 gap-2">
                      {s.files['snapshot.png'] && (
                        <img
                          src={`/api/demos/${d.name}/${s.name}/snapshot.png`}
                          alt={`${s.name} snapshot`}
                          className="w-full border border-slate-800 rounded [image-rendering:pixelated]"
                          loading="lazy"
                        />
                      )}
                      {s.files['ground_truth.png'] && (
                        <img
                          src={`/api/demos/${d.name}/${s.name}/ground_truth.png`}
                          alt={`${s.name} ground truth`}
                          className="w-full border border-slate-800 rounded [image-rendering:pixelated]"
                          loading="lazy"
                        />
                      )}
                    </div>
                  )}
                  <div className="space-y-1 text-xs">
                    {Object.entries(s.files).map(([fname, size]) => (
                      <a
                        key={fname}
                        href={`/api/demos/${d.name}/${s.name}/${fname}`}
                        download
                        className="flex justify-between items-center px-2 py-1 rounded border border-slate-800 hover:border-pwm-accent/50 hover:bg-slate-900/50 transition"
                      >
                        <code>{fname}</code>
                        <span className="text-pwm-muted">{formatBytes(size)}</span>
                      </a>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {first?.meta.how_to_run && (
              <div>
                <div className="text-xs uppercase tracking-wide text-pwm-muted mb-1">
                  Run it
                </div>
                <pre className="text-xs bg-slate-950 rounded p-3 overflow-x-auto">
                  <code>{first.meta.how_to_run}</code>
                </pre>
              </div>
            )}
          </div>
        );
      })}

      <footer className="text-xs text-pwm-muted pt-4 border-t border-slate-800 max-w-2xl">
        Demo files are regenerated from{' '}
        <code className="text-slate-400">scripts/generate_demos.py</code> at
        fixed RNG seeds — byte-stable across runs so any SHA-256 in a
        sample&apos;s <code className="text-slate-400">meta.json</code> can
        be cross-checked against the repo.
      </footer>
    </div>
  );
}
