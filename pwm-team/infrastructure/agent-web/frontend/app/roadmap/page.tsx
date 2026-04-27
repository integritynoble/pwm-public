import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Roadmap · PWM',
  description:
    'PWM development phases — U1a (done) → U1a polish (NOW) → U1b → U2 → U3. Phases gate on observable signals, not calendar dates.',
};

type ExitSignal = {
  label: string;
  target: string;
  status: 'done' | 'pending' | 'future';
};

type Phase = {
  id: string;
  title: string;
  state: 'complete' | 'now' | 'next' | 'later';
  summary: string;
  signals: ExitSignal[];
};

const PHASES: Phase[] = [
  {
    id: 'u1a',
    title: 'Phase U1a — 2 anchors verified',
    state: 'complete',
    summary:
      'CASSI + CACTI principles, specs, benchmarks, reference solvers, matcher, demos, walkthroughs all shipped.',
    signals: [
      { label: 'CASSI L1/L2/L3 live on testnet', target: '✓', status: 'done' },
      { label: 'CACTI L1/L2/L3 live on testnet', target: '✓', status: 'done' },
      { label: 'Reference solvers (GAP-TV, PnP-ADMM)', target: 'running', status: 'done' },
      { label: 'Faceted matcher on /match', target: '✓', status: 'done' },
      { label: '/demos with InverseNet KAIST-10 + SCI-Video samples', target: '✓', status: 'done' },
      { label: '/walkthroughs/{cassi,cacti}', target: '✓', status: 'done' },
      { label: '/contribute page (six paths)', target: '✓', status: 'done' },
      { label: 'G4 gate — ≥ 20 non-founder L4 submissions', target: 'pending UTSW cohort', status: 'pending' },
    ],
  },
  {
    id: 'u1a-polish',
    title: 'Phase U1a polish — make CASSI + CACTI work well',
    state: 'now',
    summary:
      'The near-term focus. Solver tuning and real-data validation before any new anchors. Driven by NEAR_TERM_CHECKLIST.md.',
    signals: [
      { label: 'CASSI PSNR on KAIST-10', target: '≥ 24 dB (current 14–19 dB)', status: 'pending' },
      { label: 'CACTI PSNR on SCI Video', target: '≥ 24 dB (current 4–13 dB)', status: 'pending' },
      { label: 'Real-data validation', target: '≥ 1 IRB-approved scene reproduced end-to-end', status: 'pending' },
      { label: 'Solver runtime, 256×256, commodity CPU', target: '< 60 s', status: 'pending' },
      { label: 'Pre-mainnet UX bugs', target: 'all resolved', status: 'pending' },
      { label: 'G4 gate (TWO_ANCHOR_MVP_LOCKED)', target: '≥ 20 non-founder L4 submissions', status: 'pending' },
    ],
  },
  {
    id: 'u1b',
    title: 'Phase U1b — 3 more anchors + translator marketplace',
    state: 'next',
    summary:
      'Once Phase U1a polish exits, expand the catalog and let third parties propose new specs/benchmarks via stake.',
    signals: [
      { label: 'MRI reconstruction anchor (L1-005)', target: 'live + ≥ 5 L4 submissions', status: 'future' },
      { label: 'CT reconstruction anchor (L1-006)', target: 'live + ≥ 5 L4 submissions', status: 'future' },
      { label: 'TEM anchor (L1-007)', target: 'live + ≥ 5 L4 submissions', status: 'future' },
      { label: 'Translator marketplace', target: '≥ 3 accepted non-founder spec/benchmark proposals', status: 'future' },
      { label: 'USD/PWM reference exchange rate', target: 'methodology published; first rate live', status: 'future' },
    ],
  },
  {
    id: 'u2',
    title: 'Phase U2 — third-party platforms',
    state: 'later',
    summary:
      '3rd-party platform SDK + full contributor mining UI. Multiple branded platforms operating concurrently.',
    signals: [
      { label: '3rd-party platform SDK', target: 'v1.0 released, audited', status: 'future' },
      { label: 'Reference 3rd-party integration', target: '≥ 1 live (e.g., UTSW clinical workflow)', status: 'future' },
      { label: 'Contributor UI in explorer', target: '/mine/{solution,benchmark,spec,principle} shipped', status: 'future' },
      { label: 'Independent 3rd-party platforms', target: '≥ 3 operating, ≥ 10K PWM/month settlement each', status: 'future' },
      { label: 'End-user volume', target: '≥ 100 unique users/platform/month', status: 'future' },
      { label: 'USD/PWM reference rate', target: 'updated daily, accepted by ≥ 2 platforms', status: 'future' },
    ],
  },
  {
    id: 'u3',
    title: 'Phase U3 — mature ecosystem',
    state: 'later',
    summary:
      'Multi-domain coverage; sustainable contributor economics; visible competition between platforms.',
    signals: [
      { label: 'Principles in catalog', target: '≥ 50 active beyond Genesis 500', status: 'future' },
      {
        label: 'Domain coverage',
        target:
          'medical imaging + materials science + structural mechanics + fluid dynamics',
        status: 'future',
      },
      { label: 'Top-decile L4 miners', target: 'sustainable income ≥ TBD USD/month', status: 'future' },
      { label: '3rd-party platform competition', target: 'visible price/UX/niche differentiation across ≥ 3 platforms', status: 'future' },
    ],
  },
];

const STATE_PILL: Record<Phase['state'], string> = {
  complete: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
  now: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40',
  next: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
  later: 'bg-slate-500/15 text-slate-400 border-slate-600',
};

const STATE_LABEL: Record<Phase['state'], string> = {
  complete: 'Complete',
  now: 'Now',
  next: 'Next',
  later: 'Later',
};

const SIGNAL_ICON: Record<ExitSignal['status'], string> = {
  done: '✓',
  pending: '⏳',
  future: '·',
};

const SIGNAL_COLOR: Record<ExitSignal['status'], string> = {
  done: 'text-emerald-400',
  pending: 'text-amber-400',
  future: 'text-slate-500',
};

export default function RoadmapPage() {
  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">PWM roadmap</h1>
        <p className="text-pwm-muted mt-2 max-w-3xl text-sm">
          Phases gate on <strong>observable signals</strong>, not calendar dates.
          Calendar estimates are advisory; the only real trigger is the exit
          criterion. A phase is &ldquo;done&rdquo; when every exit signal is
          true. Source of truth:{' '}
          <code className="text-slate-400">
            pwm-team/coordination/strategy/PWM_PRODUCT_VISION.md
          </code>{' '}
          (private repo; this page mirrors the published phase tables).
        </p>
      </header>

      {PHASES.map((phase) => (
        <section
          key={phase.id}
          className={`pwm-card ${
            phase.state === 'now' ? 'border-cyan-500/40' : ''
          }`}
        >
          <div className="flex items-baseline justify-between flex-wrap gap-3 mb-3">
            <h2 className="text-lg font-semibold">{phase.title}</h2>
            <span
              className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 border rounded ${STATE_PILL[phase.state]}`}
            >
              {STATE_LABEL[phase.state]}
            </span>
          </div>
          <p className="text-sm text-pwm-muted mb-4">{phase.summary}</p>
          <table className="pwm-table">
            <thead>
              <tr>
                <th className="w-6"></th>
                <th>Exit signal</th>
                <th>Target</th>
              </tr>
            </thead>
            <tbody>
              {phase.signals.map((s) => (
                <tr key={s.label}>
                  <td className={`font-mono ${SIGNAL_COLOR[s.status]}`}>
                    {SIGNAL_ICON[s.status]}
                  </td>
                  <td className="text-sm">{s.label}</td>
                  <td className="text-sm font-mono text-pwm-muted">{s.target}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}

      <section className="pwm-card max-w-3xl border-cyan-500/30">
        <h2 className="text-lg font-semibold mb-2">Why signals, not dates</h2>
        <p className="text-sm text-pwm-muted">
          Research-pace projects can&apos;t hit calendar deadlines without
          either cutting corners or pretending. By gating on observable signals
          (PSNR ≥ 24 dB, ≥ 20 non-founder submissions, etc.), we keep the
          schedule honest: a phase is done when the work is done, not when the
          calendar says so. Failure modes (solver tuning plateaus, cohort
          doesn&apos;t mine, etc.) have explicit contingencies — see the vision
          doc.
        </p>
      </section>

      <footer className="text-xs text-pwm-muted pt-4 border-t border-slate-800">
        Page is regenerated from the source vision doc. Update both when phase
        boundaries change. Cross-refs:{' '}
        <Link href="/contribute" className="pwm-link">
          /contribute
        </Link>
        ,{' '}
        <Link href="/walkthroughs/cassi" className="pwm-link">
          /walkthroughs/cassi
        </Link>
        ,{' '}
        <Link href="/walkthroughs/cacti" className="pwm-link">
          /walkthroughs/cacti
        </Link>
        .
      </footer>
    </div>
  );
}
