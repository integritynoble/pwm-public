import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Contribute · PWM',
  description:
    'Five contributor sections — Principle (L1), Spec (L2), Benchmark (L3), Solution (L4), and Reserve bounties. Each layer has Browse / Mine / Stake actions; solutions are work-only.',
};

// === Layer-action card schema ===
// Each layer (L1/L2/L3) has THREE actions: Browse / Mine / Stake.
// Solutions (L4) have TWO actions: Browse / Mine (solutions cannot be staked
// — they're the work product, not a slot you can register in advance).

type Action = {
  title: string;
  description: string;
  href: string;
  cta: string;
  style: 'browse' | 'mine' | 'stake';
  liveToday: boolean;
};

type LayerSection = {
  layer: 'L1' | 'L2' | 'L3' | 'L4';
  name: string;
  oneLine: string;
  paperRef: string;
  prevLayer?: { id: string; name: string };
  nextLayer?: { id: string; name: string };
  actions: Action[];
};

const SECTIONS: LayerSection[] = [
  {
    layer: 'L1',
    name: 'Principle',
    oneLine:
      'The protocol\'s "constitution" layer — six-tuple physics + L_DAG complexity, gated by S1-S4.',
    paperRef: '§3 The Principle (L1)',
    nextLayer: { id: 'spec', name: 'Spec' },
    actions: [
      {
        title: 'Browse principles',
        description:
          'See all 500 genesis principles + any post-genesis additions. Click any principle to view its forward model E, L-DAG, and the specs/benchmarks under it.',
        href: '/principles',
        cta: 'Browse →',
        style: 'browse',
        liveToday: true,
      },
      {
        title: 'Mine a new principle',
        description:
          'Draft a new principle (forward model + L_DAG + spec range) for a physics domain not in the Genesis 500. Includes the ≥ $50 stake. Submit for S1-S4 verification + sub-DAO physics review. Reserve grant on acceptance + 5% upstream royalty forever.',
        href: '#',
        cta: 'Mine (post-G4)',
        style: 'mine',
        liveToday: false,
      },
      {
        title: 'Stake a principle slot',
        description:
          'Reserve a principle slot before you start the work — useful if you need to coordinate with collaborators or want to defend a domain idea publicly. Stake ≥ $50 (PWM at 30-day TWAP, min 10 PWM). Slot held until S1-S4 submission deadline.',
        href: '#',
        cta: 'Stake (post-G4)',
        style: 'stake',
        liveToday: false,
      },
    ],
  },
  {
    layer: 'L2',
    name: 'Spec (spec.md)',
    oneLine:
      'A formal task definition under an existing Principle — six-tuple range plus an ε_fn that maps any Ω point to a minimum quality threshold.',
    paperRef: '§4 The spec.md (L2)',
    prevLayer: { id: 'principle', name: 'Principle' },
    nextLayer: { id: 'benchmark', name: 'Benchmark' },
    actions: [
      {
        title: 'Browse specs',
        description:
          'See all specs (currently surfaced as child entries of each principle on /principles/<id>). Each spec has an Ω range, ε_fn, and one or more I-benchmark tiers.',
        href: '/principles',
        cta: 'Browse →',
        style: 'browse',
        liveToday: true,
      },
      {
        title: 'Mine a new spec',
        description:
          'Pick a parent principle (promoted or genesis), draft the spec.md (YAML), submit for S1-S4 + d_spec ≥ 0.35 in-range check. Stake ≥ $5 (min 2 PWM floor). Reserve grant on acceptance + 10% upstream royalty forever.',
        href: '#',
        cta: 'Mine (post-G4)',
        style: 'mine',
        liveToday: false,
      },
      {
        title: 'Stake a spec slot',
        description:
          'Reserve a spec slot under an existing principle before drafting. Stake ≥ $5 / 2 PWM floor. Slot held until S1-S4 submission deadline.',
        href: '#',
        cta: 'Stake (post-G4)',
        style: 'stake',
        liveToday: false,
      },
    ],
  },
  {
    layer: 'L3',
    name: 'Benchmark',
    oneLine:
      'A complete, hash-committed dataset under an existing spec. Includes generator, four mismatch tiers (T1-T4), six anti-overfitting mechanisms (M1-M6), pre-computed reference baselines.',
    paperRef: '§5 The Benchmark (L3)',
    prevLayer: { id: 'spec', name: 'Spec' },
    nextLayer: { id: 'solution', name: 'Solution' },
    actions: [
      {
        title: 'Browse benchmarks',
        description:
          'See all benchmarks. Currently L3-003 (CASSI) and L3-004 (CACTI) are live with reference solvers + 16 demo samples. Three more (MRI, CT, TEM) arrive after the G4 gate.',
        href: '/benchmarks',
        cta: 'Browse →',
        style: 'browse',
        liveToday: true,
      },
      {
        title: 'Mine a new benchmark',
        description:
          'Pick a parent spec (under a promoted or genesis principle), build the dataset + thresholds (ε per tier), submit for S1-S4 + d_ibench ≥ τ in-range check. Stake ≥ $1 (min 1 PWM floor). Reserve grant on acceptance + 15% upstream royalty forever.',
        href: '#',
        cta: 'Mine (post-G4)',
        style: 'mine',
        liveToday: false,
      },
      {
        title: 'Stake a benchmark slot',
        description:
          'Reserve a benchmark slot under an existing spec before building the dataset. Stake ≥ $1 / 1 PWM floor.',
        href: '#',
        cta: 'Stake (post-G4)',
        style: 'stake',
        liveToday: false,
      },
    ],
  },
  {
    layer: 'L4',
    name: 'Solution (cert)',
    oneLine:
      'The primary mining path. A verified algorithm that solves the benchmark on K=5 unpredictable test instances. Cert is certified iff worst-case Q ≥ ε.',
    paperRef: '§6 The Solution (L4)',
    prevLayer: { id: 'benchmark', name: 'Benchmark' },
    actions: [
      {
        title: 'Browse solutions',
        description:
          'See certified L4 certs and their leaderboards. Each benchmark page has a top-10 ranking. Click any cert to verify its S1-S4 status.',
        href: '/benchmarks',
        cta: 'Browse leaderboards →',
        style: 'browse',
        liveToday: true,
      },
      {
        title: 'Mine a new solution',
        description:
          'Run pwm-node mine <benchmark> --solver your_solver.py. Protocol generates K=5 test instances, runs your solver, computes worst-case Q, certifies if Q ≥ ε. NO stake required (just gas). Earn ranked-draw share of the benchmark\'s pool. Currently working: CASSI (L3-003), CACTI (L3-004).',
        href: '/use',
        cta: 'Try the CASSI / CACTI flow →',
        style: 'mine',
        liveToday: true,
      },
      // No "stake" action for L4 — solutions are work-product, not stakeable slots.
    ],
  },
];

const STYLE_PILL: Record<Action['style'], string> = {
  browse: 'border-slate-700 text-pwm-muted',
  mine: 'border-cyan-500/40 text-cyan-400',
  stake: 'border-amber-500/40 text-amber-400',
};

export default function ContributePage() {
  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Contribute to PWM</h1>
        <p className="text-sm text-pwm-muted mt-2 max-w-3xl">
          Five contributor sections, organized by the four-layer artifact
          hierarchy plus Reserve bounties for infrastructure. Each layer has
          three actions — <strong>Browse</strong> what exists,{' '}
          <strong>Mine</strong> a new one, <strong>Stake</strong> a slot.{' '}
          <strong>
            Solutions (L4) have only two actions — solutions cannot be staked,
            because they are the work product, not a registerable slot.
          </strong>{' '}
          Source: pwm_overview1.md §3-§6 + §10.
        </p>
      </header>

      {/* Current focus banner */}
      <section className="pwm-card border-cyan-500/30 bg-cyan-950/10">
        <div className="flex items-baseline justify-between flex-wrap gap-2">
          <div>
            <span className="text-[10px] uppercase tracking-wide text-cyan-400">
              Current focus
            </span>
            <p className="text-sm mt-1">
              For now, only <strong>CASSI</strong> (L3-003) and{' '}
              <strong>CACTI</strong> (L3-004) are live for solution mining.
              New principles, specs, and benchmarks become creatable after the
              G4 gate clears (≥ 20 non-founder L4 submissions). See the{' '}
              <Link href="/roadmap" className="pwm-link">
                roadmap
              </Link>
              .
            </p>
          </div>
        </div>
      </section>

      {/* Layer flow visualization */}
      <section className="pwm-card max-w-3xl">
        <h2 className="text-sm font-semibold mb-2 uppercase tracking-wide text-pwm-muted">
          Four-layer flow (browseable in either direction)
        </h2>
        <div className="flex items-center gap-2 flex-wrap text-sm">
          <a href="#principle" className="px-3 py-1.5 rounded bg-slate-900/60 border border-slate-700 hover:border-pwm-accent">
            <strong>L1</strong> Principle
          </a>
          <span className="text-pwm-muted">↔</span>
          <a href="#spec" className="px-3 py-1.5 rounded bg-slate-900/60 border border-slate-700 hover:border-pwm-accent">
            <strong>L2</strong> Spec
          </a>
          <span className="text-pwm-muted">↔</span>
          <a href="#benchmark" className="px-3 py-1.5 rounded bg-slate-900/60 border border-slate-700 hover:border-pwm-accent">
            <strong>L3</strong> Benchmark
          </a>
          <span className="text-pwm-muted">↔</span>
          <a href="#solution" className="px-3 py-1.5 rounded bg-slate-900/60 border border-slate-700 hover:border-pwm-accent">
            <strong>L4</strong> Solution
          </a>
          <span className="text-pwm-muted mx-2">·</span>
          <a href="#bounty" className="px-3 py-1.5 rounded bg-slate-900/60 border border-slate-700 hover:border-pwm-accent">
            <strong>Bounty</strong>
          </a>
        </div>
      </section>

      {/* Per-layer sections */}
      {SECTIONS.map((s) => (
        <LayerSectionCard key={s.layer} section={s} />
      ))}

      <BountySection />

      <footer className="text-xs text-pwm-muted pt-4 border-t border-slate-800">
        Reference doc:{' '}
        <code className="text-slate-400">
          pwm-team/coordination/CONTRIBUTOR_ONBOARDING.md
        </code>
        . Stake floors and earnings model from{' '}
        <code className="text-slate-400">
          papers/Proof-of-Solution/pwm_overview1.md
        </code>{' '}
        §3-§6 + §10 (Three-Tier Staking System).
      </footer>
    </div>
  );
}


function LayerSectionCard({ section: s }: { section: LayerSection }) {
  return (
    <section id={s.layer === 'L1' ? 'principle' : s.layer === 'L2' ? 'spec' : s.layer === 'L3' ? 'benchmark' : 'solution'} className="space-y-4 max-w-5xl">
      <div className="flex items-baseline justify-between flex-wrap gap-3">
        <h2 className="text-xl font-semibold">
          <span className="font-mono text-pwm-accent">{s.layer}</span> · {s.name}
        </h2>
        <span className="text-[10px] uppercase tracking-wide text-pwm-muted">
          {s.paperRef}
        </span>
      </div>
      <p className="text-sm text-pwm-muted max-w-3xl">{s.oneLine}</p>

      <div className={`grid gap-3 ${s.actions.length === 2 ? 'md:grid-cols-2' : 'md:grid-cols-3'}`}>
        {s.actions.map((a) => (
          <ActionCard key={a.title} action={a} />
        ))}
      </div>

      {/* Cross-navigation between layers */}
      <div className="flex items-center gap-3 text-sm flex-wrap pt-2 border-t border-slate-800">
        {s.prevLayer && (
          <a
            href={`#${s.prevLayer.id}`}
            className="text-pwm-muted hover:text-pwm-accent"
          >
            ← {s.prevLayer.name}
          </a>
        )}
        {s.nextLayer && (
          <a
            href={`#${s.nextLayer.id}`}
            className="text-pwm-muted hover:text-pwm-accent ml-auto"
          >
            {s.nextLayer.name} →
          </a>
        )}
      </div>
    </section>
  );
}


function ActionCard({ action: a }: { action: Action }) {
  return (
    <div className="pwm-card flex flex-col">
      <div className="flex items-center gap-2 mb-2">
        <span
          className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 border rounded ${STYLE_PILL[a.style]}`}
        >
          {a.style}
        </span>
        {a.liveToday ? (
          <span className="text-[10px] uppercase tracking-wide text-emerald-400">
            ● live
          </span>
        ) : (
          <span className="text-[10px] uppercase tracking-wide text-slate-500">
            ○ post-G4
          </span>
        )}
      </div>
      <h3 className="font-semibold">{a.title}</h3>
      <p className="text-sm text-pwm-muted mt-2 flex-1">{a.description}</p>
      <div className="mt-3">
        {a.liveToday ? (
          <Link
            href={a.href}
            className="inline-block px-3 py-1.5 rounded bg-gradient-to-r from-cyan-500 to-indigo-500 text-black font-semibold text-sm"
          >
            {a.cta}
          </Link>
        ) : (
          <span
            className="inline-block px-3 py-1.5 rounded border border-slate-700 text-sm text-slate-500 cursor-not-allowed"
            title="Available after Phase U1b — see /roadmap"
          >
            {a.cta}
          </span>
        )}
      </div>
    </div>
  );
}


function BountySection() {
  return (
    <section id="bounty" className="space-y-3 max-w-5xl">
      <div className="flex items-baseline justify-between flex-wrap gap-3">
        <h2 className="text-xl font-semibold">
          Bounty · for infrastructure
        </h2>
        <span className="text-[10px] uppercase tracking-wide text-pwm-muted">
          §11 Reserve allocation
        </span>
      </div>
      <p className="text-sm text-pwm-muted max-w-3xl">
        Reserve bounties pay PWM tokens for building <strong>competing
        implementations</strong> of the protocol&apos;s infrastructure.
        Different from layer-mining: bounties don&apos;t require stake to
        participate, and they reward engineering on the platform rather than
        physics or science. Eight bounties total (~1.238M PWM); four open
        today.
      </p>
      <div className="pwm-card overflow-x-auto">
        <table className="pwm-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Bounty</th>
              <th>Reward</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {[
              ['1', 'Scoring engine (competing impl)', '200,000 PWM', 'OPEN'],
              ['2', 'Web UI / Explorer', '80,000 PWM', 'OPEN'],
              ['3', 'pwm-node CLI', '100,000 PWM', 'OPEN'],
              ['4', 'Mining client (CP)', '80,000 PWM', 'OPEN'],
              ['5', 'Contracts (competing impl)', '500,000 PWM', 'Phase 1 sign-off'],
              ['6', 'IPFS benchmark pinning', '50,000 PWM', 'Phase 1 sign-off'],
              ['7', 'Genesis Principle Polish (v2 — pool-weight + 60/40 split)', '~168,000 PWM', 'Phase 2 + 7d'],
              ['8', 'LLM-routed matcher', '60,000 PWM', 'After TWO_ANCHOR_MVP_LOCKED'],
            ].map((row) => {
              const isOpen = row[3] === 'OPEN';
              return (
                <tr key={row[0]}>
                  <td className="font-mono text-pwm-muted">{row[0]}</td>
                  <td>{row[1]}</td>
                  <td className="font-mono">{row[2]}</td>
                  <td>
                    <span
                      className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 border rounded ${
                        isOpen
                          ? 'border-emerald-500/40 text-emerald-400'
                          : 'border-slate-600 text-slate-500'
                      }`}
                    >
                      {row[3]}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="pt-2">
        <Link
          href="/bounties"
          className="inline-block px-3 py-1.5 rounded bg-gradient-to-r from-cyan-500 to-indigo-500 text-black font-semibold text-sm"
        >
          See full bounty specs →
        </Link>
      </div>
      <div className="pt-2">
        <a
          href="#solution"
          className="text-pwm-muted hover:text-pwm-accent text-sm"
        >
          ← Back to Solution (L4)
        </a>
      </div>
    </section>
  );
}
