import { api } from '@/lib/api';
import { ApiDown, Empty } from '@/components/Empty';

export default async function BountiesPage() {
  const data = await api.bounties();
  if (!data) return <ApiDown />;

  const total = data.bounties.reduce((acc, b) => acc + (b.amount_pwm ?? 0), 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Open bounties</h1>
        <p className="text-pwm-muted mt-2">
          Reserve pool allocations for third-party implementations. Total open:{' '}
          <span className="font-mono text-pwm-accent">{total.toLocaleString()} PWM</span>.
        </p>
      </div>

      {data.bounties.length === 0 ? (
        <Empty>No bounty specs published yet. Check back once agent-coord publishes INDEX.md.</Empty>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {data.bounties.map((b) => (
            <article key={b.slug} className="pwm-card flex flex-col">
              <header className="flex items-baseline justify-between gap-3">
                <h2 className="text-lg font-semibold">{b.title}</h2>
                {b.amount_pwm != null && (
                  <span className="pwm-pill !text-pwm-accent !border-pwm-accent">
                    {b.amount_pwm.toLocaleString()} PWM
                  </span>
                )}
              </header>
              <p className="text-sm text-pwm-muted mt-2 flex-1">{b.summary || '—'}</p>
              <p className="text-xs font-mono text-slate-500 mt-3">{b.spec_path}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
