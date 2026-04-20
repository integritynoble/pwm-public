import Link from 'next/link';
import { api } from '@/lib/api';
import { ApiDown } from '@/components/Empty';
import { shortAddr, weiToPwm } from '@/lib/format';

export default async function BenchmarksPage() {
  const data = await api.benchmarks();
  if (!data) return <ApiDown />;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Benchmarks</h1>

      <section>
        <h2 className="text-lg font-semibold mb-3">Genesis (off-chain JSON)</h2>
        {data.genesis.length === 0 ? (
          <div className="pwm-card text-pwm-muted italic">No L3 JSONs published yet.</div>
        ) : (
          <div className="pwm-card overflow-x-auto">
            <table className="pwm-table">
              <thead>
                <tr><th>ID</th><th>Title</th><th>Principle</th><th>Domain</th><th>ρ</th><th>ε</th></tr>
              </thead>
              <tbody>
                {data.genesis.map((b) => (
                  <tr key={b.artifact_id}>
                    <td className="font-mono">
                      <Link className="pwm-link" href={`/benchmarks/${b.artifact_id}`}>{b.artifact_id}</Link>
                    </td>
                    <td>{b.title ?? '—'}</td>
                    <td>
                      {b.parent_l1 ? (
                        <Link className="pwm-link font-mono" href={`/principles/${b.parent_l1}`}>{b.parent_l1}</Link>
                      ) : '—'}
                    </td>
                    <td>{b.domain ?? '—'}</td>
                    <td>{b.rho ?? '—'}</td>
                    <td>{b.epsilon ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">On-chain (indexed)</h2>
        {data.chain.length === 0 ? (
          <div className="pwm-card text-pwm-muted italic">No L3 artifacts registered on-chain yet.</div>
        ) : (
          <div className="pwm-card overflow-x-auto">
            <table className="pwm-table">
              <thead>
                <tr><th>Hash</th><th>Creator</th><th>Pool balance</th><th>Block</th></tr>
              </thead>
              <tbody>
                {data.chain.map((b) => (
                  <tr key={b.hash}>
                    <td className="font-mono">
                      <Link className="pwm-link" href={`/benchmarks/${b.hash}`}>{shortAddr(b.hash)}</Link>
                    </td>
                    <td className="font-mono">{shortAddr(b.creator)}</td>
                    <td>{weiToPwm(b.pool_balance_wei)} PWM</td>
                    <td>{b.block_number}</td>
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
