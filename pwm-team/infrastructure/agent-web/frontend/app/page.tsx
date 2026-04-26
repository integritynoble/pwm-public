import Link from 'next/link';
import { api } from '@/lib/api';
import { shortAddr, timeAgo, weiToPwm } from '@/lib/format';
import { ActivityFeed } from '@/components/ActivityFeed';
import { ApiDown } from '@/components/Empty';

export default async function HomePage() {
  const overview = await api.overview();
  if (!overview) return <ApiDown />;

  const stats = [
    { label: 'Minting pool remaining', value: `${weiToPwm(overview.total_pool_wei)} PWM` },
    { label: 'Active principles', value: overview.active_principles.toLocaleString() },
    { label: 'Benchmarks indexed', value: overview.counts.benchmarks.toLocaleString() },
    { label: 'Certificates submitted', value: overview.counts.certificates.toLocaleString() },
    { label: 'Draws settled', value: overview.counts.draws.toLocaleString() },
  ];

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold tracking-tight">Physics World Model Explorer</h1>
        <p className="text-pwm-muted mt-2 max-w-3xl">
          A public, read-only view of the PWM protocol. <strong>Two main functions:</strong>{' '}
          use a verified solution for your data, or contribute to the protocol as a
          miner / bounty hunter. Third-party platforms can layer on as compute
          providers + payment gateways. No wallet required to browse.
        </p>
      </section>

      <PhaseStatusBanner />

      <section className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="pwm-card">
            <div className="text-xs uppercase tracking-wide text-pwm-muted">{s.label}</div>
            <div className="text-2xl font-semibold mt-1">{s.value}</div>
          </div>
        ))}
      </section>

      {overview.recent_draws.length > 0 && (
        <section>
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="text-xl font-semibold">Recent draws</h2>
            <Link href="/benchmarks" className="pwm-link text-sm">Browse benchmarks →</Link>
          </div>
          <div className="pwm-card overflow-x-auto">
            <table className="pwm-table">
              <thead>
                <tr>
                  <th>When</th>
                  <th>Cert</th>
                  <th>Benchmark</th>
                  <th>Rank</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {overview.recent_draws.map((d) => (
                  <tr key={d.cert_hash}>
                    <td>{timeAgo(d.settled_at)}</td>
                    <td className="font-mono">
                      <Link className="pwm-link" href={`/cert/${d.cert_hash}`}>{shortAddr(d.cert_hash)}</Link>
                    </td>
                    <td className="font-mono">
                      <Link className="pwm-link" href={`/leaderboard/${d.benchmark_hash}`}>{shortAddr(d.benchmark_hash)}</Link>
                    </td>
                    <td>#{d.rank}</td>
                    <td>{weiToPwm(d.draw_amount)} PWM</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section>
        <div className="flex items-baseline justify-between mb-3">
          <h2 className="text-xl font-semibold">Activity feed</h2>
          <Link href="/benchmarks" className="pwm-link text-sm">Browse benchmarks →</Link>
        </div>
        <ActivityFeed entries={overview.recent_activity ?? []} />
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-3">How to engage with PWM</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <Link href="/match" className="pwm-card hover:border-pwm-accent transition-colors block">
            <div className="text-2xl font-black text-pwm-accent">1</div>
            <h3 className="font-semibold text-lg mt-1">Use a solution →</h3>
            <p className="text-sm text-pwm-muted mt-1">
              Describe your data; the matcher routes you to the right benchmark.
              See 2 example samples (measurement / ground truth / reconstruction)
              and run the reference solver on your own input.
            </p>
            <span className="inline-block mt-2 text-[10px] uppercase tracking-wide px-1.5 py-0.5 border border-emerald-500/40 text-emerald-400 rounded">
              live · no wallet
            </span>
          </Link>

          <Link href="/contribute" className="pwm-card hover:border-pwm-accent transition-colors block">
            <div className="text-2xl font-black text-pwm-accent">2</div>
            <h3 className="font-semibold text-lg mt-1">Become a contributor →</h3>
            <p className="text-sm text-pwm-muted mt-1">
              Mine solutions for ranked-draw rewards (no stake). Or stake PWM to
              propose new principles, specs, or benchmarks and earn long-tail
              upstream cuts. Plus 8 Reserve bounties (~1.238M PWM) for
              competing infrastructure.
            </p>
            <span className="inline-block mt-2 text-[10px] uppercase tracking-wide px-1.5 py-0.5 border border-emerald-500/40 text-emerald-400 rounded">
              4 of 8 bounties open
            </span>
          </Link>

          <div className="pwm-card border-slate-800 opacity-80">
            <div className="text-2xl font-black text-pwm-muted">3</div>
            <h3 className="font-semibold text-lg mt-1 text-pwm-muted">
              Build a third-party platform
            </h3>
            <p className="text-sm text-pwm-muted mt-1">
              Compute provider + payment gateway role. Charge end users in USD
              or PWM at your own exchange rate; settle to the protocol in PWM.
              SDK arrives in Phase U2 — see the{' '}
              <Link href="/contribute" className="pwm-link">
                role definition
              </Link>{' '}
              + reference exchange rate methodology.
            </p>
            <span className="inline-block mt-2 text-[10px] uppercase tracking-wide px-1.5 py-0.5 border border-slate-600 text-slate-500 rounded">
              Phase U2 (post-G4)
            </span>
          </div>
        </div>
        <p className="text-xs text-pwm-muted mt-3 max-w-3xl">
          Two anchors live today —{' '}
          <Link href="/principles/L1-003" className="pwm-link">CASSI</Link> and{' '}
          <Link href="/principles/L1-004" className="pwm-link">CACTI</Link>. Three more
          (MRI, CT, TEM) arrive after the G4 gate. Full plan + exit signals on the{' '}
          <Link href="/roadmap" className="pwm-link">roadmap</Link>.
        </p>
      </section>
    </div>
  );
}


function PhaseStatusBanner() {
  return (
    <section className="pwm-card border-cyan-500/30 bg-cyan-950/10">
      <div className="flex items-baseline justify-between flex-wrap gap-3">
        <div className="flex-1 min-w-0">
          <span className="text-[10px] uppercase tracking-wide text-cyan-400">
            Current phase
          </span>
          <h3 className="font-semibold mt-0.5">
            U1a polish — making CASSI + CACTI work well
          </h3>
          <p className="text-xs text-pwm-muted mt-1 max-w-3xl">
            Near-term focus is solver-quality + real-data validation on the two
            anchors before adding new principles. G4 gate (≥ 20 non-founder L4
            submissions) is the only behavioral signal still pending.
          </p>
        </div>
        <Link href="/roadmap" className="pwm-link text-sm shrink-0">
          See roadmap →
        </Link>
      </div>
    </section>
  );
}
