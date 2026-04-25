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
