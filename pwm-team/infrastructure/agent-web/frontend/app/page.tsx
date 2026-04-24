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
          A public, read-only view of the PWM protocol — 500 genesis physics principles, their
          benchmarks, pool balances, and settled draws. No wallet required.
        </p>
      </section>

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

      <section className="grid md:grid-cols-2 gap-4">
        <Link href="/principles" className="pwm-card hover:border-pwm-accent transition-colors">
          <h3 className="font-semibold text-lg">Browse 500 principles →</h3>
          <p className="text-sm text-pwm-muted mt-1">
            L1 physics principles with their forward models, L_DAG diagrams, and active benchmarks.
          </p>
        </Link>
        <Link href="/bounties" className="pwm-card hover:border-pwm-accent transition-colors">
          <h3 className="font-semibold text-lg">Reserve bounties →</h3>
          <p className="text-sm text-pwm-muted mt-1">
            1,238,000 PWM across 8 bounties — 4 open now (460,000 PWM), 4 open on milestones.
          </p>
        </Link>
      </section>
    </div>
  );
}
