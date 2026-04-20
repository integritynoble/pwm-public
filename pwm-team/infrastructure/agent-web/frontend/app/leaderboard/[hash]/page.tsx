import Link from 'next/link';
import { notFound } from 'next/navigation';
import { api } from '@/lib/api';
import { shortAddr, timeAgo, weiToPwm } from '@/lib/format';
import { StatusBadge } from '@/components/Badges';

export default async function LeaderboardPage({ params }: { params: Promise<{ hash: string }> }) {
  const { hash } = await params;
  const data = await api.leaderboard(hash);
  if (!data) return notFound();

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/benchmarks/${hash}`} className="pwm-link text-sm">← Benchmark detail</Link>
        <h1 className="text-3xl font-bold tracking-tight mt-2">Leaderboard</h1>
        <p className="text-pwm-muted font-mono text-sm break-all">{data.benchmark_hash}</p>
      </div>

      {data.entries.length === 0 ? (
        <div className="pwm-card text-pwm-muted italic">No solutions yet.</div>
      ) : (
        <div className="pwm-card overflow-x-auto">
          <table className="pwm-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Cert</th>
                <th>Submitter</th>
                <th>Q</th>
                <th>Status</th>
                <th>Draw</th>
                <th>Settled</th>
              </tr>
            </thead>
            <tbody>
              {data.entries.map((c: any, i: number) => (
                <tr key={c.cert_hash}>
                  <td className="font-semibold">#{c.draw_rank ?? i + 1}</td>
                  <td className="font-mono">
                    <Link href={`/cert/${c.cert_hash}`} className="pwm-link">{shortAddr(c.cert_hash)}</Link>
                  </td>
                  <td className="font-mono">{shortAddr(c.submitter)}</td>
                  <td>{c.q_int}</td>
                  <td><StatusBadge status={c.status} /></td>
                  <td>{c.draw_amount ? `${weiToPwm(c.draw_amount)} PWM` : '—'}</td>
                  <td>{timeAgo(c.settled_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
