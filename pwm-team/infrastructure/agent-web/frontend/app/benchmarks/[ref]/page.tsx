import Link from 'next/link';
import { notFound } from 'next/navigation';
import { api } from '@/lib/api';
import { shortAddr, weiToPwm } from '@/lib/format';
import { StatusBadge } from '@/components/Badges';

export default async function BenchmarkDetail({ params }: { params: Promise<{ ref: string }> }) {
  const { ref } = await params;
  const data = await api.benchmark(ref);
  if (!data) return notFound();

  const g = data.genesis;
  const chain = data.chain;
  const tier = g?.ibenchmark_range?.center_ibenchmark ?? {};
  const bounds = g?.ibenchmark_range?.tier_bounds ?? {};
  const baselines = g?.protocol_fields?.baselines ?? [];

  const chainHashForLeaderboard = chain?.hash;

  return (
    <div className="space-y-8">
      <div>
        <Link href="/benchmarks" className="pwm-link text-sm">← All benchmarks</Link>
        <h1 className="text-3xl font-bold tracking-tight mt-2">
          {g?.title ?? ref}
          <span className="text-pwm-muted text-lg ml-3">{g?.artifact_id ?? shortAddr(ref)}</span>
        </h1>
      </div>

      <section className="grid md:grid-cols-2 gap-4">
        <div className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">Genesis spec</h2>
          {g ? (
            <dl className="text-sm space-y-1">
              <div><dt className="inline text-pwm-muted">Parent L2:</dt> <dd className="inline ml-2 font-mono">{g.parent_l2 ?? '—'}</dd></div>
              <div><dt className="inline text-pwm-muted">Spec type:</dt> <dd className="inline ml-2">{g.spec_type ?? '—'}</dd></div>
              <div><dt className="inline text-pwm-muted">d_spec:</dt> <dd className="inline ml-2">{g.d_spec ?? '—'}</dd></div>
              {tier.rho != null && <div><dt className="inline text-pwm-muted">ρ:</dt> <dd className="inline ml-2">{tier.rho}</dd></div>}
              {tier.epsilon != null && <div><dt className="inline text-pwm-muted">ε:</dt> <dd className="inline ml-2">{tier.epsilon}</dd></div>}
            </dl>
          ) : (
            <p className="text-pwm-muted italic text-sm">No off-chain spec linked.</p>
          )}
        </div>

        <div className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">On-chain</h2>
          {chain ? (
            <dl className="text-sm space-y-1">
              <div><dt className="inline text-pwm-muted">Hash:</dt> <dd className="inline ml-2 font-mono break-all">{chain.hash}</dd></div>
              <div><dt className="inline text-pwm-muted">Creator:</dt> <dd className="inline ml-2 font-mono">{shortAddr(chain.creator)}</dd></div>
              <div><dt className="inline text-pwm-muted">Block:</dt> <dd className="inline ml-2">{chain.block_number}</dd></div>
              <div><dt className="inline text-pwm-muted">Pool:</dt> <dd className="inline ml-2">{weiToPwm(data.pool_balance_wei)} PWM</dd></div>
            </dl>
          ) : (
            <p className="text-pwm-muted italic text-sm">Not registered on-chain yet.</p>
          )}
        </div>
      </section>

      {Object.keys(tier).length > 0 && (
        <section className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">Ω tier</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            {Object.entries(tier.omega_tier ?? {}).map(([k, v]) => (
              <div key={k} className="bg-slate-950/60 border border-slate-800 rounded px-2 py-1">
                <div className="text-xs text-pwm-muted">{k}</div>
                <div className="font-mono">{String(v)}</div>
                {bounds[k] && (
                  <div className="text-[10px] text-slate-500 font-mono">∈ [{bounds[k][0]}, {bounds[k][1]}]</div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {baselines.length > 0 && (
        <section className="pwm-card">
          <h2 className="text-lg font-semibold mb-2">Baselines</h2>
          <table className="pwm-table">
            <thead>
              <tr><th>Name</th><th>Method</th><th>Expected PSNR</th></tr>
            </thead>
            <tbody>
              {baselines.map((b: any) => (
                <tr key={b.name}>
                  <td>{b.name}</td>
                  <td className="font-mono text-xs">{b.method_sig}</td>
                  <td>{b.expected_psnr} dB</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section>
        <div className="flex items-baseline justify-between mb-3">
          <h2 className="text-lg font-semibold">Leaderboard (top 10)</h2>
          {chainHashForLeaderboard && (
            <Link href={`/leaderboard/${chainHashForLeaderboard}`} className="pwm-link text-sm">
              Full leaderboard →
            </Link>
          )}
        </div>
        {data.leaderboard.length === 0 ? (
          <div className="pwm-card text-pwm-muted italic">No solutions submitted yet.</div>
        ) : (
          <div className="pwm-card overflow-x-auto">
            <table className="pwm-table">
              <thead>
                <tr><th>Rank</th><th>Cert</th><th>Submitter</th><th>Q</th><th>Status</th><th>Draw</th></tr>
              </thead>
              <tbody>
                {data.leaderboard.map((c: any, i: number) => (
                  <tr key={c.cert_hash}>
                    <td>{c.draw_rank ?? `#${i + 1}?`}</td>
                    <td className="font-mono">
                      <Link className="pwm-link" href={`/cert/${c.cert_hash}`}>{shortAddr(c.cert_hash)}</Link>
                    </td>
                    <td className="font-mono">{shortAddr(c.submitter)}</td>
                    <td>{c.q_int}</td>
                    <td><StatusBadge status={c.status} /></td>
                    <td>{c.draw_amount ? `${weiToPwm(c.draw_amount)} PWM` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
