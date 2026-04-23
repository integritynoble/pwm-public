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
          (&lt; 50 KB each), deterministic. Download the input, run the
          reference solver locally, and see the full PWM mining pipeline
          work in under a minute. <strong>These are not the real
          benchmarks.</strong> They exist so newcomers can verify the
          pipeline end-to-end before burning gas on a real{' '}
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

      {data.demos.map((d) => (
        <div key={d.name} className="pwm-card space-y-4">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="text-xs text-pwm-muted uppercase tracking-wide">
                {d.meta.tier_approx ?? ''}
              </div>
              <h2 className="text-xl font-semibold mt-1 font-mono">
                {d.name}
              </h2>
              <p className="text-sm text-pwm-muted mt-1">
                {d.meta.benchmark}
              </p>
            </div>
            {d.meta.reference_solver_psnr_db !== undefined && (
              <div className="text-right text-sm">
                <div className="text-xs text-pwm-muted">reference PSNR</div>
                <div className="text-xl font-semibold text-pwm-accent">
                  {d.meta.reference_solver_psnr_db.toFixed(1)} dB
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
              {d.meta.shape_snapshot && (
                <div>snapshot: [{d.meta.shape_snapshot.join(', ')}]</div>
              )}
              {d.meta.shape_ground_truth && (
                <div>ground truth: [{d.meta.shape_ground_truth.join(', ')}]</div>
              )}
              {d.meta.shape_solution && (
                <div>reference solution: [{d.meta.shape_solution.join(', ')}]</div>
              )}
            </div>
          </div>

          <div>
            <div className="text-xs uppercase tracking-wide text-pwm-muted mb-2">
              Files
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {Object.entries(d.files).map(([fname, size]) => (
                <a
                  key={fname}
                  href={`/api/demos/${d.name}/${fname}`}
                  className="flex justify-between items-center px-3 py-2 rounded border border-slate-800 hover:border-pwm-accent/50 hover:bg-slate-900/50 transition"
                >
                  <code className="text-sm">{fname}</code>
                  <span className="text-xs text-pwm-muted">
                    {formatBytes(size)}
                  </span>
                </a>
              ))}
            </div>
          </div>

          {d.meta.how_to_run && (
            <div>
              <div className="text-xs uppercase tracking-wide text-pwm-muted mb-1">
                Run it
              </div>
              <pre className="text-xs bg-slate-950 rounded p-3 overflow-x-auto">
                <code>{d.meta.how_to_run}</code>
              </pre>
            </div>
          )}
        </div>
      ))}

      <footer className="text-xs text-pwm-muted pt-4 border-t border-slate-800 max-w-2xl">
        Demo files are regenerated from{' '}
        <code className="text-slate-400">scripts/generate_demos.py</code> at
        a fixed RNG seed — they're byte-stable across runs so any SHA-256
        in a demo's <code className="text-slate-400">meta.json</code> can
        be cross-checked against the repo.
      </footer>
    </div>
  );
}
