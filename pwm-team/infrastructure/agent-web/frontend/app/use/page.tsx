import type { Metadata } from 'next';
import Link from 'next/link';
import { api } from '@/lib/api';

export const metadata: Metadata = {
  title: 'Use a Solution · PWM',
  description:
    'Find a PWM-validated solution for your data. Describe what you have; the matcher routes you to the right benchmark; preview measurement / ground-truth / reconstruction; run the reference solver locally.',
};

export const dynamic = 'force-dynamic';

const ANCHORS = [
  {
    id: 'L3-003',
    principleId: 'L1-003',
    walkthrough: 'cassi',
    name: 'CASSI',
    title: 'Coded Aperture Snapshot Spectral Imaging',
    summary:
      'Reconstruct a 28-band hyperspectral image cube from a single 2D coded-aperture snapshot.',
    inputShape: '256 × 256 (snapshot)',
    outputShape: '256 × 256 × 28 (HSI cube)',
    refSolver: 'GAP-TV',
    sampleCount: 10,
    sampleSource: 'KAIST-10',
  },
  {
    id: 'L3-004',
    principleId: 'L1-004',
    walkthrough: 'cacti',
    name: 'CACTI',
    title: 'Coded Aperture Compressive Temporal Imaging',
    summary:
      'Reconstruct an 8-frame video block from a single 2D temporal-coded snapshot.',
    inputShape: '256 × 256 (snapshot)',
    outputShape: '256 × 256 × 8 (video)',
    refSolver: 'PnP-ADMM',
    sampleCount: 6,
    sampleSource: 'SCI Video Benchmark',
  },
];

export default async function UseSolutionPage() {
  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Use a Solution</h1>
        <p className="text-pwm-muted mt-2 max-w-3xl text-sm">
          Find a PWM-validated solution for your data in three steps:
          (1) describe what you have, (2) preview the matched benchmark&apos;s
          example data, (3) run the reference solver on your own input.
          No wallet required.
        </p>
      </header>

      {/* Step 1: Match form */}
      <section>
        <div className="flex items-baseline gap-3 mb-3">
          <span className="text-2xl font-black text-pwm-accent">1</span>
          <h2 className="text-xl font-semibold">Describe your data</h2>
        </div>

        <form method="GET" action="/match" className="pwm-card max-w-3xl space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">Free-text prompt</label>
            <textarea
              name="prompt"
              placeholder='e.g. "I have a CASSI snapshot, 256×256, mild calibration drift, noise ~2%, need a hyperspectral cube out"'
              rows={3}
              className="w-full rounded bg-slate-900/60 border border-slate-700 px-3 py-2 text-sm"
            />
          </div>
          <div className="flex items-center gap-3">
            <button
              type="submit"
              className="px-4 py-2 rounded bg-gradient-to-r from-cyan-500 to-indigo-500 text-black font-semibold text-sm"
            >
              Match
            </button>
            <Link href="/match" className="text-sm text-pwm-muted hover:text-pwm-accent">
              Open full matcher with structured filters →
            </Link>
          </div>
        </form>
        <p className="text-xs text-pwm-muted mt-2 max-w-3xl">
          The faceted matcher is deterministic (no LLM). It checks your prompt
          against benchmark cards using keyword + filter scoring. A score
          ≥ 2.0 returns matching benchmarks; below that you&apos;ll be invited
          to propose a new spec via the Contribute path.
        </p>
      </section>

      {/* Step 2: Available solutions */}
      <section>
        <div className="flex items-baseline gap-3 mb-3">
          <span className="text-2xl font-black text-pwm-accent">2</span>
          <h2 className="text-xl font-semibold">Or browse what&apos;s already validated</h2>
        </div>
        <p className="text-sm text-pwm-muted mb-4 max-w-3xl">
          Two anchors live on testnet today. Three more (MRI, CT, TEM) arrive
          after the G4 gate — see the{' '}
          <Link href="/roadmap" className="pwm-link">
            roadmap
          </Link>
          .
        </p>

        <div className="grid md:grid-cols-2 gap-4">
          {ANCHORS.map((a) => (
            <div key={a.id} className="pwm-card space-y-3">
              <div>
                <div className="flex items-baseline justify-between flex-wrap gap-2">
                  <h3 className="text-lg font-semibold">{a.name}</h3>
                  <span className="font-mono text-xs text-pwm-muted">
                    {a.principleId} → {a.id}
                  </span>
                </div>
                <p className="text-sm text-pwm-muted mt-1">{a.title}</p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <img
                  src={`/api/demos/${a.walkthrough}/sample_01/snapshot.png`}
                  alt={`${a.name} sample measurement`}
                  className="w-full border border-slate-800 rounded bg-slate-950 [image-rendering:pixelated]"
                  loading="lazy"
                />
                <img
                  src={`/api/demos/${a.walkthrough}/sample_01/ground_truth.png`}
                  alt={`${a.name} sample ground truth`}
                  className="w-full border border-slate-800 rounded bg-slate-950 [image-rendering:pixelated]"
                  loading="lazy"
                />
              </div>

              <p className="text-sm">{a.summary}</p>

              <dl className="text-xs grid grid-cols-2 gap-y-1">
                <dt className="text-pwm-muted">Input shape</dt>
                <dd className="font-mono">{a.inputShape}</dd>
                <dt className="text-pwm-muted">Output shape</dt>
                <dd className="font-mono">{a.outputShape}</dd>
                <dt className="text-pwm-muted">Reference solver</dt>
                <dd className="font-mono">{a.refSolver}</dd>
                <dt className="text-pwm-muted">Samples available</dt>
                <dd className="font-mono">
                  {a.sampleCount} ({a.sampleSource})
                </dd>
              </dl>

              <div className="flex gap-2 pt-1 flex-wrap">
                <Link
                  href={`/benchmarks/${a.id}`}
                  className="px-3 py-1.5 rounded bg-gradient-to-r from-cyan-500 to-indigo-500 text-black font-semibold text-sm"
                >
                  Try this benchmark →
                </Link>
                <Link
                  href={`/walkthroughs/${a.walkthrough}`}
                  className="px-3 py-1.5 rounded border border-slate-700 text-sm text-pwm-muted hover:text-pwm-accent hover:border-pwm-accent"
                >
                  Read 4-layer walkthrough
                </Link>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap gap-3 text-sm">
          <Link href="/match" className="pwm-link">
            Full matcher →
          </Link>
          <Link href="/demos" className="pwm-link">
            All 16 demo samples →
          </Link>
          <Link href="/benchmarks" className="pwm-link">
            All benchmarks →
          </Link>
          <Link href="/principles" className="pwm-link">
            Browse principles →
          </Link>
        </div>
      </section>

      {/* Step 3: Run locally */}
      <section>
        <div className="flex items-baseline gap-3 mb-3">
          <span className="text-2xl font-black text-pwm-accent">3</span>
          <h2 className="text-xl font-semibold">Run the reference solver locally</h2>
        </div>
        <p className="text-sm text-pwm-muted mb-3 max-w-3xl">
          Once you&apos;ve picked a benchmark, copy-paste the snippet on its{' '}
          <code className="text-slate-400">Get this benchmark</code> card.
          For CASSI/L3-003 it looks like:
        </p>
        <pre className="bg-slate-950 border border-slate-800 rounded px-3 py-3 text-xs overflow-x-auto max-w-3xl">
{`git clone https://github.com/integritynoble/Physics_World_Model.git
cd Physics_World_Model
python3 pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py \\
    --input  pwm-team/pwm_product/demos/cassi/sample_01 \\
    --output /tmp/out
cat /tmp/out/meta.json
# Expect PSNR around the value in the demo's meta.json (byte-stable
# across runs at the same git SHA)`}
        </pre>
      </section>

      {/* Footer */}
      <section className="pwm-card max-w-3xl border-cyan-500/30">
        <h3 className="font-semibold">Found nothing that matches?</h3>
        <p className="text-sm text-pwm-muted mt-2">
          PWM&apos;s catalog is the Genesis 500 (locked) plus translator-proposed
          principles (post-mainnet). If your problem isn&apos;t covered, you can
          stake to propose a new principle / spec / benchmark — that&apos;s the
          contributor path.
        </p>
        <Link
          href="/contribute"
          className="inline-block mt-3 px-3 py-1.5 rounded border border-slate-700 text-sm text-pwm-muted hover:text-pwm-accent hover:border-pwm-accent"
        >
          See the contributor paths →
        </Link>
      </section>
    </div>
  );
}
