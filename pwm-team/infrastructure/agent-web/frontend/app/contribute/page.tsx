import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Contribute · PWM',
  description:
    'Six paths to participate in PWM — from running the reference solver on your own data, to claiming a Reserve bounty, to mining solutions for PWM tokens.',
};

const PATHS = [
  {
    id: 1,
    name: 'Just use PWM',
    audience: 'Researchers, clinicians',
    wallet: 'No',
    cost: '$0',
    reward: 'Reproducibility, paper citations',
    live: 'live',
  },
  {
    id: 2,
    name: 'Reserve bounty',
    audience: 'Engineers, scientists with engineering chops',
    wallet: 'Yes (to receive payment)',
    cost: 'Engineering time',
    reward: '50,000 – 500,000 PWM per bounty',
    live: 'live (4 of 8 open)',
  },
  {
    id: 3,
    name: 'Mine PWM',
    audience: 'Solver authors',
    wallet: 'Yes',
    cost: '~$5 ETH gas + optional PWM stake',
    reward: 'Rank-weighted draws from per-benchmark pool',
    live: 'testnet',
  },
  {
    id: 4,
    name: 'Compute Provider (CP)',
    audience: 'Anyone with idle compute',
    wallet: 'Yes',
    cost: 'PWM bond + electricity',
    reward: 'Per-job fee',
    live: 'testnet',
  },
  {
    id: 5,
    name: 'Translator (propose new benchmarks)',
    audience: 'Domain experts',
    wallet: 'Yes',
    cost: 'PWM stake',
    reward: '5/10/15% upstream cut',
    live: 'post-mainnet',
  },
  {
    id: 6,
    name: 'Observe / hold / community',
    audience: 'Investors, supporters',
    wallet: 'Optional',
    cost: '$0',
    reward: 'Governance vote, appreciation',
    live: 'live',
  },
] as const;

const STATUS_PILL: Record<string, string> = {
  live: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
  'live (4 of 8 open)': 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
  testnet: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
  'post-mainnet': 'bg-slate-500/20 text-slate-400 border-slate-600',
};

export default function ContributePage() {
  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">How to contribute to PWM</h1>
        <p className="text-sm text-pwm-muted mt-2 max-w-3xl">
          PWM has six distinct paths to participate, ranked from
          &ldquo;lowest commitment&rdquo; to &ldquo;deepest economic role.&rdquo;
          Most contributors only ever use one or two. Pick the one that
          matches what you have (data, code, compute, or just curiosity).
        </p>
      </header>

      <section className="pwm-card overflow-x-auto">
        <table className="pwm-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Path</th>
              <th>Audience</th>
              <th>Wallet?</th>
              <th>Cost</th>
              <th>Reward</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {PATHS.map((p) => (
              <tr key={p.id}>
                <td className="font-mono text-pwm-muted">{p.id}</td>
                <td className="font-semibold">{p.name}</td>
                <td className="text-sm">{p.audience}</td>
                <td className="text-sm">{p.wallet}</td>
                <td className="text-sm">{p.cost}</td>
                <td className="text-sm">{p.reward}</td>
                <td>
                  <span
                    className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 border rounded ${STATUS_PILL[p.live]}`}
                  >
                    {p.live}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="space-y-6 max-w-4xl">
        <PathCard
          n={1}
          title="Just use PWM"
          subtitle="The starting point for almost everyone — researchers comparing methods, clinicians running solvers on real data, students reproducing PWM benchmarks."
        >
          <ol className="list-decimal list-inside space-y-1 text-sm">
            <li>
              <Link href="/match" className="pwm-link">
                /match
              </Link>{' '}
              — type your data description, get matching benchmarks
            </li>
            <li>
              Click <strong>&ldquo;Try this benchmark →&rdquo;</strong> on the top result;
              lands at <code className="text-slate-400">/benchmarks/L3-003</code>
            </li>
            <li>
              <strong>&ldquo;Get this benchmark&rdquo;</strong> card → download{' '}
              <code className="text-slate-400">snapshot.npz</code> /{' '}
              <code className="text-slate-400">ground_truth.npz</code>
            </li>
            <li>
              Clone the public repo + run the reference solver locally (one
              copy-paste command on the page)
            </li>
            <li>
              Read{' '}
              <Link href="/walkthroughs/cassi" className="pwm-link">
                /walkthroughs/cassi
              </Link>{' '}
              for the full physics → benchmark → solution story
            </li>
          </ol>
          <p className="text-xs text-pwm-muted mt-3">
            <strong>Wallet:</strong> none. <strong>Cost:</strong> $0.{' '}
            <strong>What you get:</strong> reference solver running on your
            laptop, the same scoring framework PWM uses on-chain, and
            reproducible PSNR/SSIM numbers you can cite in a paper.
          </p>
        </PathCard>

        <PathCard
          n={2}
          title="Reserve bounty"
          subtitle="Highest cash reward; serious engineering. 8 bounties totaling ~1,238,000 PWM."
        >
          <p className="text-sm mb-2">
            See{' '}
            <Link href="/bounties" className="pwm-link">
              /bounties
            </Link>{' '}
            for the full list. Steps:
          </p>
          <ol className="list-decimal list-inside space-y-1 text-sm">
            <li>Read the bounty spec</li>
            <li>
              Open a GitHub Discussion at{' '}
              <code className="text-slate-400">integritynoble/Physics_World_Model</code>
              :{' '}
              <code className="text-slate-400">
                [BOUNTY-N] claim intent — &lt;your team&gt;
              </code>
            </li>
            <li>
              Fork, build to spec, pass the reference test harness (every
              bounty&apos;s <code>tests/</code> dir is the acceptance harness)
            </li>
            <li>Open a PR with wallet address + test-run evidence</li>
            <li>
              30-day shadow run alongside the reference; correctness or
              availability regressions can void the award
            </li>
            <li>PWM lands in your wallet</li>
          </ol>
          <p className="text-xs text-pwm-muted mt-3">
            <strong>Wallet:</strong> required (to receive payment).{' '}
            <strong>Cost:</strong> 1-3 months engineering for a typical bounty.{' '}
            <strong>What you get:</strong> PWM tokens directly + reputation as
            a foundational PWM contributor.
          </p>
        </PathCard>

        <PathCard
          n={3}
          title="Mine PWM"
          subtitle="The flagship economic loop. Submit L4 solutions to existing benchmarks; earn from per-benchmark pools."
        >
          <ol className="list-decimal list-inside space-y-1 text-sm">
            <li>
              Install the <code className="text-slate-400">pwm-node</code> CLI
            </li>
            <li>
              <code className="text-slate-400">pwm-node init</code> — generates
              wallet; fund with testnet ETH from Sepolia faucet
            </li>
            <li>
              <code className="text-slate-400">
                pwm-node mine L3-003 --solver your_solver.py
              </code>
            </li>
            <li>
              CLI runs your solver on the benchmark, computes the cert hash,
              submits via PWMCertificate.submit
            </li>
            <li>
              PWMReward.distribute pays out per the rank-draw schedule (Rank 1
              = 40% of the per-event amount)
            </li>
          </ol>
          <p className="text-xs text-pwm-muted mt-3">
            <strong>Wallet:</strong> required. <strong>Cost on Base mainnet:</strong>{' '}
            ~$0.05/tx in gas, optional artifact stakes (10/2/1 PWM at L1/L2/L3).{' '}
            <strong>What you get:</strong> rank-weighted PWM draws from every
            benchmark pool you place in. <strong>Live on testnet today.</strong>
          </p>
        </PathCard>

        <PathCard
          n={4}
          title="Compute Provider (CP)"
          subtitle="Sell idle compute. Run others' solvers in a sandboxed Docker container, earn per-job fees."
        >
          <ol className="list-decimal list-inside space-y-1 text-sm">
            <li>
              Pull <code className="text-slate-400">pwm-sandbox:latest</code>{' '}
              container (network-isolated, read-only filesystem)
            </li>
            <li>
              <code className="text-slate-400">pwm-miner cp register</code> —
              stakes a CP bond (slashable for misbehavior)
            </li>
            <li>Listen for job offers via the JobQueue contract; accept ones you can run within the time budget</li>
            <li>
              Execute the solver in the sandbox; return the cert hash
            </li>
            <li>Earn the per-job fee on each successfully delivered cert</li>
          </ol>
          <p className="text-xs text-pwm-muted mt-3">
            <strong>Cost:</strong> CP bond (slashable) + electricity + uptime.{' '}
            <strong>What you get:</strong> steady per-job fee income from
            solver authors who want elastic compute.
          </p>
        </PathCard>

        <PathCard
          n={5}
          title="Translator — propose new benchmarks"
          subtitle="Add a new physics principle to the catalog (post-mainnet only). For domain experts whose research field has no PWM principle yet."
        >
          <ol className="list-decimal list-inside space-y-1 text-sm">
            <li>Stake PWM (slashable if S1-S4 verification fails)</li>
            <li>
              Draft new L1 + L2 + L3 artifacts using the four-layer template
              from{' '}
              <Link href="/walkthroughs/cassi" className="pwm-link">
                /walkthroughs/cassi
              </Link>{' '}
              as reference
            </li>
            <li>
              Submit to the on-chain registry; verifier agents (physics,
              numerics, cross-domain) review against S1-S4 gates
            </li>
            <li>
              If accepted, your principle joins the live catalog and starts
              earning rewards from every L4 solution submitted under it
            </li>
            <li>Earn 5/10/15% upstream cut of each L4 event automatically</li>
          </ol>
          <p className="text-xs text-pwm-muted mt-3">
            <strong>Wallet:</strong> required. <strong>Cost:</strong> PWM stake.{' '}
            <strong>What you get:</strong> long-tail royalty on every solution
            under your principle + reputation as a domain authority.
          </p>
          <p className="text-xs text-amber-400 mt-2">
            ⚠ Genesis 500 principles are locked at protocol launch. This path
            is for adding new principles AFTER mainnet.
          </p>
        </PathCard>

        <PathCard
          n={6}
          title="Observe / hold / community"
          subtitle="Watch and participate without committing capital or code yet."
        >
          <ul className="list-disc list-inside space-y-1 text-sm">
            <li>
              Browse{' '}
              <Link href="/" className="pwm-link">
                the explorer
              </Link>{' '}
              — live activity feed, pool sizes, recent draws
            </li>
            <li>
              Follow{' '}
              <a
                href="https://github.com/integritynoble/Physics_World_Model/discussions"
                target="_blank"
                rel="noreferrer"
                className="pwm-link"
              >
                GitHub Discussions
              </a>{' '}
              for protocol announcements
            </li>
            <li>
              (Post-mainnet) Hold PWM — vote on governance proposals via{' '}
              <code className="text-slate-400">PWMGovernance</code>
            </li>
            <li>Attend community events (workshops, MICCAI tutorial)</li>
          </ul>
          <p className="text-xs text-pwm-muted mt-3">
            <strong>Cost:</strong> $0. <strong>What you get:</strong>{' '}
            governance participation post-mainnet; first-mover position when
            new bounties open.
          </p>
        </PathCard>
      </section>

      <LayerMiningSection />

      <section className="pwm-card max-w-4xl border-cyan-500/30">
        <h2 className="text-lg font-semibold mb-2">Three honest filters to choose</h2>
        <ol className="list-decimal list-inside space-y-2 text-sm">
          <li>
            <strong>Have data but not engineering bandwidth?</strong> → Path 1
            (use). 95% of academic users start here.
          </li>
          <li>
            <strong>Have engineering bandwidth + want PWM tokens?</strong> →
            Path 2 (bounty). Quickest path to meaningful PWM income.
          </li>
          <li>
            <strong>Have a novel solver that beats baselines?</strong> → Path 3
            (mine). The flagship economic loop.
          </li>
        </ol>
        <p className="text-xs text-pwm-muted mt-4">
          Other paths layer on top of these once mainnet is live. Today,
          Paths 1, 2, and 6 are the ones to act on; Paths 3-5 are
          testnet-only or post-mainnet.
        </p>
      </section>

      <footer className="text-xs text-pwm-muted pt-4 border-t border-slate-800">
        Source:{' '}
        <code className="text-slate-400">
          pwm-team/coordination/CONTRIBUTOR_ONBOARDING.md
        </code>
        . For the full reference document with academic checklist + cross-references, see that file in the repo.
      </footer>
    </div>
  );
}


function PathCard({
  n,
  title,
  subtitle,
  children,
}: {
  n: number;
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="pwm-card">
      <div className="flex items-baseline gap-3 mb-2">
        <span className="text-2xl font-black text-pwm-accent">{n}</span>
        <h2 className="text-lg font-semibold">{title}</h2>
      </div>
      <p className="text-sm text-pwm-muted mb-4">{subtitle}</p>
      {children}
    </div>
  );
}


// === L1-L4 mining-by-layer ===
// Source: papers/Proof-of-Solution/pwm_overview1.md §3-§6 (per-layer
// definitions) + §10 "Token Economics" → Three-Tier Staking System
// + §6 "L4 Solution: Primary Mining Path".

const LAYERS: Array<{
  layer: 'L1' | 'L2' | 'L3' | 'L4';
  name: string;
  short: string;
  longDescription: string;
  mineableHow: string;
  stakeUSD: string;
  stakePWMFloor: string;
  earnFrom: string;
  paperRef: string;
  canStake: boolean;
}> = [
  {
    layer: 'L1',
    name: 'Principle',
    short: 'A new physics principle',
    longDescription:
      'The protocol\'s "constitution layer" — a six-tuple (Ω, E, B, I, O, ε) describing the physics of a problem class plus the L_DAG complexity score. Must pass the 10 Physics-Validity tests (P1–P10) and S1–S4 mathematical gates.',
    mineableHow:
      'Stake PWM, draft the principle (forward model + L_DAG + spec range), submit for S1–S4 verification + sub-DAO physics review. Reserve grant on acceptance (DAO-voted). Plus 5% upstream royalty on every L4 event under your principle, forever.',
    stakeUSD: '≥ $50',
    stakePWMFloor: 'min 10 PWM',
    earnFrom: 'Reserve grant (DAO vote at S4) + 5% upstream cut from every L4 event under this principle',
    paperRef: '§3 The Principle (L1): Physics Foundation',
    canStake: true,
  },
  {
    layer: 'L2',
    name: 'Spec (spec.md)',
    short: 'A formal task definition under an existing Principle',
    longDescription:
      'A six-tuple (Ω-range, E-bound, B-bound, I-bound, O-bound, ε-fn) that pins one task within a Principle. Must include an ε_fn that maps any Ω point to a minimum acceptable quality threshold, plus an I-benchmark range that defines the canonical evaluation point.',
    mineableHow:
      'Stake PWM, draft the spec.md (YAML), submit for S1–S4 + d_spec ≥ 0.35 in-range check. Reserve grant on acceptance. Plus 10% upstream royalty on every L4 event under your spec.',
    stakeUSD: '≥ $5',
    stakePWMFloor: 'min 2 PWM',
    earnFrom: 'Reserve grant (DAO vote at S4 + d_spec ≥ 0.35) + 10% upstream cut from every L4 event under this spec',
    paperRef: '§4 The spec.md (L2): Formal Task Definition',
    canStake: true,
  },
  {
    layer: 'L3',
    name: 'Benchmark',
    short: 'A complete, hash-committed dataset under an existing spec',
    longDescription:
      'A self-contained dataset enabling trustless verification of solutions. Includes generator code, test instances at multiple resolutions (M2 convergence), four mismatch tiers (T1 nominal → T4 blind), six anti-overfitting mechanisms (M1–M6), and pre-computed reference baselines.',
    mineableHow:
      'Stake PWM, build the dataset + thresholds (ε per tier), submit for S1–S4 + d_ibench ≥ τ in-range check. Reserve grant on acceptance. Plus 15% upstream royalty on every L4 event scored against your benchmark.',
    stakeUSD: '≥ $1',
    stakePWMFloor: 'min 1 PWM',
    earnFrom: 'Reserve grant (DAO vote at S4 + d_ibench ≥ τ) + 15% upstream cut from every L4 event under this benchmark',
    paperRef: '§5 The Benchmark (L3): Verification Infrastructure',
    canStake: true,
  },
  {
    layer: 'L4',
    name: 'Solution (cert)',
    short: 'A solver submission for an existing benchmark',
    longDescription:
      'The primary mining path. A verified algorithm that solves the benchmark on K=5 unpredictable test instances drawn at submission time from G(SHA256(h_submission ‖ k)). Cert is certified iff worst-case Q = min_i(score_i) ≥ ε. SP (= AC) holds the slot, CP runs the binary; sub-split is `p × 55%` SP / `(1−p) × 55%` CP.',
    mineableHow:
      'No stake required for one-shot cert submission (just gas). Run `pwm-node mine <benchmark> --solver your_solver.py`; protocol generates K=5 test instances, runs your solver, computes worst-case Q, certifies if Q ≥ ε. Optionally register as long-running SP / CP (≥ $50 / ≥ $5) to earn ongoing usage fees.',
    stakeUSD: 'None for cert submission · ≥ $50 (SP) · ≥ $5 (CP) post-U1b',
    stakePWMFloor: 'gas only · 50 / 5 PWM floors',
    earnFrom: 'Ranked-draw share of the benchmark\'s pool — `p × 55%` to SP, `(1−p) × 55%` to CP, `15%` to T_k principle treasury, remainder to Reserve',
    paperRef: '§6 The Solution (L4): Primary Mining Path',
    canStake: false,
  },
];


function LayerMiningSection() {
  return (
    <section className="space-y-4 max-w-4xl">
      <div>
        <h2 className="text-xl font-semibold">Mining by layer (L1 / L2 / L3 / L4)</h2>
        <p className="text-sm text-pwm-muted mt-2">
          The four-layer artifact hierarchy is the protocol&apos;s core
          structure. Each layer is mineable but with different stake/earn
          rules. <strong>Solutions can only be mined</strong> (no stake
          required to create — they are the work product). Principles, specs,
          and benchmarks can both be{' '}
          <em>created via stake</em> and <em>used to earn upstream royalties</em>.
          Stake floors are USD-denominated; PWM amounts adjust at the 30-day
          TWAP. Source:{' '}
          <a
            href="https://github.com/integritynoble/Physics_World_Model/blob/master/papers/Proof-of-Solution/pwm_overview1.md"
            target="_blank"
            rel="noreferrer"
            className="pwm-link"
          >
            pwm_overview1.md
          </a>{' '}
          §3–§6 + §10.
        </p>
      </div>

      {/* Quick comparison table */}
      <div className="pwm-card overflow-x-auto">
        <table className="pwm-table">
          <thead>
            <tr>
              <th>Layer</th>
              <th>What</th>
              <th>Stake to create?</th>
              <th>Stake floor</th>
              <th>Earn from</th>
            </tr>
          </thead>
          <tbody>
            {LAYERS.map((L) => (
              <tr key={L.layer}>
                <td className="font-mono font-semibold">{L.layer}</td>
                <td>{L.name}</td>
                <td>
                  {L.canStake ? (
                    <span className="text-emerald-400">✓ yes</span>
                  ) : (
                    <span className="text-amber-400">✗ no — only mineable</span>
                  )}
                </td>
                <td className="font-mono text-xs">
                  {L.stakeUSD}{' '}
                  <span className="text-pwm-muted">/ {L.stakePWMFloor}</span>
                </td>
                <td className="text-xs">{L.earnFrom.split(' + ')[0]}…</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Per-layer detail cards */}
      <div className="space-y-3">
        {LAYERS.map((L) => (
          <div key={L.layer} className="pwm-card">
            <div className="flex items-baseline justify-between flex-wrap gap-2 mb-2">
              <h3 className="font-semibold">
                <span className="font-mono text-pwm-accent">{L.layer}</span>{' '}
                · {L.name}{' '}
                <span className="text-sm text-pwm-muted font-normal">
                  — {L.short}
                </span>
              </h3>
              <span className="text-[10px] uppercase tracking-wide text-pwm-muted">
                {L.paperRef}
              </span>
            </div>

            <p className="text-sm mt-2">{L.longDescription}</p>

            <div className="grid md:grid-cols-3 gap-3 mt-3 text-xs">
              <div className="bg-slate-950/40 border border-slate-800 rounded p-2">
                <div className="text-[10px] uppercase tracking-wide text-pwm-muted mb-1">
                  Stake floor
                </div>
                <div className="font-mono">{L.stakeUSD}</div>
                <div className="font-mono text-pwm-muted">{L.stakePWMFloor}</div>
              </div>
              <div className="bg-slate-950/40 border border-slate-800 rounded p-2">
                <div className="text-[10px] uppercase tracking-wide text-pwm-muted mb-1">
                  How to mine
                </div>
                <div>{L.mineableHow}</div>
              </div>
              <div className="bg-slate-950/40 border border-slate-800 rounded p-2">
                <div className="text-[10px] uppercase tracking-wide text-pwm-muted mb-1">
                  Earn from
                </div>
                <div>{L.earnFrom}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Stake fate + caveats */}
      <div className="pwm-card text-sm space-y-2 border-amber-500/30">
        <h3 className="font-semibold">Stake fate (L1 / L2 / L3 only)</h3>
        <ul className="list-disc list-inside text-pwm-muted text-xs space-y-1">
          <li>
            <strong>On graduation</strong> (your artifact promoted from
            contributor-funded to protocol-funded): 50% returned to your
            wallet · 50% locked as permanent B-pool seed for the artifact.
          </li>
          <li>
            <strong>On challenge upheld</strong> (someone proves your
            artifact violates S1–S4): 50% burned · 50% to challenger ·
            artifact delisted.
          </li>
          <li>
            <strong>On fraud</strong> (deliberate violation): 100% burned ·
            artifact permanently delisted.
          </li>
        </ul>
        <p className="text-xs text-pwm-muted pt-2 border-t border-slate-800">
          <strong>Genesis 500 are locked at protocol launch.</strong> All
          principle-creation paths above are for adding the 501st principle
          and beyond, post-mainnet. Genesis principles are auto-promoted at
          launch with no staking required.
        </p>
      </div>
    </section>
  );
}
