import Link from 'next/link';
import { notFound } from 'next/navigation';
import { api } from '@/lib/api';
import { shortAddr, timeAgo, weiToPwm } from '@/lib/format';
import { StatusBadge } from '@/components/Badges';


/** Visual rank badge (matches /benchmarks/[ref] convention). */
function rankBadge(rank: number | null | undefined): string {
  if (rank == null) return '#?';
  if (rank === 1) return '🥇 #1';
  if (rank === 2) return '🥈 #2';
  if (rank === 3) return '🥉 #3';
  if (rank <= 10) return `🎗 #${rank}`;
  return `#${rank}`;
}


export default async function LeaderboardPage({ params }: { params: Promise<{ hash: string }> }) {
  const { hash } = await params;
  const data = await api.leaderboard(hash);
  if (!data) return notFound();

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/benchmarks/${hash}`} className="pwm-link text-sm">← Benchmark detail</Link>
        <h1 className="text-3xl font-bold tracking-tight mt-2">
          Leaderboard
          {data.benchmark_title && (
            <span className="text-pwm-muted text-lg ml-3">— {data.benchmark_title}</span>
          )}
        </h1>
        <p className="text-pwm-muted font-mono text-sm break-all">
          {data.benchmark_id ? `${data.benchmark_id} · ` : ''}
          {data.benchmark_hash}
        </p>
      </div>

      {data.ranks.length === 0 ? (
        <div className="pwm-card text-pwm-muted italic">No solutions yet.</div>
      ) : (
        <div className="pwm-card overflow-x-auto">
          <table className="pwm-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Solver</th>
                <th>PSNR</th>
                <th>Cert</th>
                <th>Submitter</th>
                <th>Q</th>
                <th>Status</th>
                <th>Draw</th>
                <th>Settled</th>
              </tr>
            </thead>
            <tbody>
              {data.ranks.map((c: any) => (
                <tr key={c.cert_hash}>
                  <td className="font-semibold">{rankBadge(c.rank)}</td>
                  <td>
                    {c.solver_label ?? <span className="text-pwm-muted italic">—</span>}
                  </td>
                  <td className="font-mono">
                    {c.psnr_db != null
                      ? `${Number(c.psnr_db).toFixed(1)} dB`
                      : <span className="text-pwm-muted italic">—</span>}
                  </td>
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
