import Link from 'next/link';
import { api } from '@/lib/api';
import { ApiDown } from '@/components/Empty';
import { shortAddr, weiToPwm } from '@/lib/format';

function bar(balanceWei: string, max: bigint): string {
  try {
    if (max === 0n) return 'w-0';
    const pct = Number((BigInt(balanceWei) * 100n) / max);
    return `w-[${Math.max(2, Math.min(100, pct))}%]`;
  } catch {
    return 'w-0';
  }
}

export default async function PoolsPage() {
  const data = await api.pools();
  if (!data) return <ApiDown />;

  const maxPool = data.pools.reduce(
    (acc, p) => (BigInt(p.balance || '0') > acc ? BigInt(p.balance || '0') : acc),
    0n
  );
  const maxTreasury = data.treasury.reduce(
    (acc, t) => (BigInt(t.balance || '0') > acc ? BigInt(t.balance || '0') : acc),
    0n
  );

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold tracking-tight">Pools</h1>

      <section>
        <h2 className="text-lg font-semibold mb-3">Benchmark pools (Pool_k)</h2>
        {data.pools.length === 0 ? (
          <div className="pwm-card text-pwm-muted italic">No pool seed events yet.</div>
        ) : (
          <div className="pwm-card space-y-2">
            {data.pools
              .slice()
              .sort((a, b) => Number(BigInt(b.balance || '0') - BigInt(a.balance || '0')))
              .map((p) => (
                <div key={p.benchmark_hash} className="flex items-center gap-3">
                  <Link href={`/leaderboard/${p.benchmark_hash}`} className="pwm-link font-mono text-sm shrink-0 w-40">
                    {shortAddr(p.benchmark_hash)}
                  </Link>
                  <div className="flex-1 bg-slate-900/60 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-2 bg-gradient-to-r from-cyan-500 to-indigo-500"
                      style={{ width: `${maxPool === 0n ? 0 : Number((BigInt(p.balance || '0') * 100n) / maxPool)}%` }}
                    />
                  </div>
                  <div className="w-40 text-right font-mono text-sm">{weiToPwm(p.balance)} PWM</div>
                </div>
              ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Principle treasuries (T_k)</h2>
        {data.treasury.length === 0 ? (
          <div className="pwm-card text-pwm-muted italic">No treasury events yet.</div>
        ) : (
          <div className="pwm-card space-y-2">
            {data.treasury
              .slice()
              .sort((a, b) => Number(BigInt(b.balance || '0') - BigInt(a.balance || '0')))
              .map((t) => (
                <div key={t.principle_id} className="flex items-center gap-3">
                  <span className="font-mono text-sm shrink-0 w-40">L1-{t.principle_id.padStart(3, '0')}</span>
                  <div className="flex-1 bg-slate-900/60 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-2 bg-gradient-to-r from-emerald-500 to-cyan-500"
                      style={{ width: `${maxTreasury === 0n ? 0 : Number((BigInt(t.balance || '0') * 100n) / maxTreasury)}%` }}
                    />
                  </div>
                  <div className="w-40 text-right font-mono text-sm">{weiToPwm(t.balance)} PWM</div>
                </div>
              ))}
          </div>
        )}
      </section>
    </div>
  );
}
