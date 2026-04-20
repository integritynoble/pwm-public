import Link from 'next/link';
import { notFound } from 'next/navigation';
import { api } from '@/lib/api';
import { GateBadge, StatusBadge } from '@/components/Badges';
import { shortAddr, STATUS_LABELS, timeAgo, weiToPwm } from '@/lib/format';

export default async function CertificatePage({ params }: { params: Promise<{ hash: string }> }) {
  const { hash } = await params;
  const data = await api.cert(hash);
  if (!data) return notFound();

  const c = data.certificate;

  const rewardRows = [
    { label: 'AC (Author/Creator)', addr: c.ac_addr, amount: c.ac_amount },
    { label: 'CP (Compute Provider)', addr: c.cp_addr, amount: c.cp_amount },
    { label: 'Treasury (T_k)', addr: null, amount: c.treasury_amount },
  ].filter((r) => r.amount);

  return (
    <div className="space-y-8">
      <div>
        <Link href="/benchmarks" className="pwm-link text-sm">← Benchmarks</Link>
        <h1 className="text-3xl font-bold tracking-tight mt-2">Certificate</h1>
        <p className="text-pwm-muted font-mono text-sm break-all mt-1">{c.cert_hash}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <StatusBadge status={c.status} />
          <span className="pwm-pill">Q = {c.q_int}/100</span>
          {c.finalized_rank != null && <span className="pwm-pill">Rank #{c.finalized_rank}</span>}
          <span className="pwm-pill">submitted {timeAgo(c.submitted_at)}</span>
        </div>
      </div>

      <section className="pwm-card">
        <h2 className="text-lg font-semibold mb-3">S1 – S4 gates</h2>
        <div className="flex gap-3 flex-wrap">
          {(['S1', 'S2', 'S3', 'S4'] as const).map((g) => (
            <div key={g} className="flex items-center gap-2">
              <span className="font-mono text-sm">{g}</span>
              <GateBadge verdict={data.s_gates[g]} />
            </div>
          ))}
        </div>
        <p className="text-xs text-pwm-muted mt-3 italic">
          Verdicts shown are derived from the certificate lifecycle. Once the scoring engine
          publishes per-gate results on-chain, each verdict will come with a detailed justification.
        </p>
      </section>

      <section className="pwm-card">
        <h2 className="text-lg font-semibold mb-3">Reward breakdown</h2>
        {rewardRows.length === 0 ? (
          <p className="text-pwm-muted italic text-sm">Not yet paid out — waiting for draw settlement.</p>
        ) : (
          <table className="pwm-table">
            <thead>
              <tr><th>Role</th><th>Address</th><th>Amount</th></tr>
            </thead>
            <tbody>
              {rewardRows.map((r) => (
                <tr key={r.label}>
                  <td>{r.label}</td>
                  <td className="font-mono">{r.addr ? shortAddr(r.addr) : '—'}</td>
                  <td>{weiToPwm(r.amount)} PWM</td>
                </tr>
              ))}
              {c.draw_amount && (
                <tr>
                  <td className="font-semibold">Total draw</td>
                  <td className="font-mono">—</td>
                  <td className="font-semibold">{weiToPwm(c.draw_amount)} PWM</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </section>

      <section className="grid md:grid-cols-2 gap-4">
        <div className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">Participants</h2>
          <dl className="text-sm space-y-1">
            <div><dt className="inline text-pwm-muted">Submitter:</dt> <dd className="inline ml-2 font-mono">{shortAddr(c.submitter)}</dd></div>
            {c.challenger && <div><dt className="inline text-pwm-muted">Challenger:</dt> <dd className="inline ml-2 font-mono">{shortAddr(c.challenger)}</dd></div>}
          </dl>
        </div>
        <div className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">Benchmark</h2>
          <div className="text-sm">
            <Link href={`/benchmarks/${c.benchmark_hash}`} className="pwm-link font-mono break-all">
              {c.benchmark_hash}
            </Link>
          </div>
          {data.benchmark_genesis && (
            <p className="text-sm text-pwm-muted mt-2">
              {data.benchmark_genesis.title} ({data.benchmark_genesis.artifact_id})
            </p>
          )}
        </div>
      </section>

      <section className="pwm-card text-sm">
        <h2 className="text-lg font-semibold mb-2">Challenge window</h2>
        <p className="text-pwm-muted">
          Status: <span className="font-mono">{STATUS_LABELS[c.status]}</span>
          {c.challenge_upheld != null && (
            <> — challenge {c.challenge_upheld ? 'upheld' : 'rejected'}.</>
          )}
        </p>
      </section>
    </div>
  );
}
