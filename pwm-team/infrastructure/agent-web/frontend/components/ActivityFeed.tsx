import Link from 'next/link';
import type { ActivityEntry } from '@/lib/api';
import { shortAddr, timeAgo, weiToPwm } from '@/lib/format';

/** Per-event presentation config. Keep it data-driven so adding a new kind
 *  means a single row here, not a new branch in the JSX. */
const KIND_LABELS: Record<string, { label: string; color: string }> = {
  artifact_registered: { label: 'Artifact registered', color: 'text-cyan-300' },
  benchmark_registered: { label: 'Benchmark registered', color: 'text-emerald-300' },
  certificate_submitted: { label: 'Certificate submitted', color: 'text-indigo-300' },
  draw_settled: { label: 'Draw settled', color: 'text-amber-300' },
  pool_seeded: { label: 'Pool seeded', color: 'text-emerald-300' },
  treasury_received: { label: 'Treasury received', color: 'text-emerald-300' },
  treasury_bounty_paid: { label: 'Bounty paid', color: 'text-amber-300' },
  stake_staked: { label: 'Registration bond', color: 'text-cyan-300' },
  stake_graduated: { label: 'Graduated', color: 'text-emerald-300' },
  stake_challenge_upheld: { label: 'Challenge upheld', color: 'text-rose-300' },
  stake_fraud_slashed: { label: 'Fraud slashed', color: 'text-rose-300' },
  minted: { label: 'Minted', color: 'text-amber-300' },
};

function link(entry: ActivityEntry): string | null {
  const h = entry.primary_hash;
  if (!h) return null;
  if (!h.startsWith('0x')) return null;
  switch (entry.kind) {
    case 'certificate_submitted':
    case 'draw_settled':
      return `/cert/${h}`;
    case 'benchmark_registered':
    case 'pool_seeded':
    case 'minted':
    case 'stake_staked':
    case 'stake_graduated':
    case 'stake_challenge_upheld':
    case 'stake_fraud_slashed':
      return `/benchmarks/${h}`;
    default:
      return null;
  }
}

function describe(entry: ActivityEntry): string {
  switch (entry.kind) {
    case 'draw_settled':
      return `Rank #${entry.layer ?? '?'} — ${weiToPwm(entry.amount)} PWM`;
    case 'pool_seeded':
      return `${weiToPwm(entry.amount)} PWM (${entry.extra ?? 'seed'})`;
    case 'minted':
      return `${weiToPwm(entry.amount)} PWM → L1-${String(entry.extra || '?').padStart(3, '0')}`;
    case 'benchmark_registered':
      return `ρ = ${entry.amount} · L1-${String(entry.extra || '?').padStart(3, '0')}`;
    case 'certificate_submitted':
      return `Q = ${entry.amount}/100`;
    case 'treasury_received':
    case 'treasury_bounty_paid':
      return `${weiToPwm(entry.amount)} PWM · L1-${String(entry.primary_hash || '?').padStart(3, '0')}`;
    case 'stake_staked':
      return `${weiToPwm(entry.amount)} PWM bond (L${entry.layer ?? '?'})`;
    case 'stake_graduated':
      return `Returned ${weiToPwm(entry.amount)} PWM`;
    case 'stake_challenge_upheld':
      return `Burned ${weiToPwm(entry.extra)} PWM`;
    case 'stake_fraud_slashed':
      return `${weiToPwm(entry.amount)} PWM burned`;
    case 'artifact_registered':
      return `L${entry.layer} artifact`;
    default:
      return entry.amount ? `${weiToPwm(entry.amount)} PWM` : '';
  }
}

export function ActivityFeed({ entries }: { entries: ActivityEntry[] }) {
  if (!entries.length) {
    return (
      <div className="pwm-card text-pwm-muted italic">
        No on-chain activity yet. The indexer will populate this as artifacts are
        registered and solved.
      </div>
    );
  }
  return (
    <div className="pwm-card overflow-x-auto">
      <ol className="space-y-3">
        {entries.map((e, i) => {
          const meta = KIND_LABELS[e.kind] ?? { label: e.kind, color: 'text-slate-300' };
          const href = link(e);
          const hashDisplay = e.primary_hash ? shortAddr(e.primary_hash) : '—';
          return (
            <li key={`${e.kind}-${e.block_number}-${i}`} className="flex gap-3 items-baseline">
              <span className={`pwm-pill !bg-slate-950 !border-slate-800 font-semibold ${meta.color}`}>
                {meta.label}
              </span>
              <div className="flex-1 text-sm">
                <div className="font-mono">
                  {href ? <Link className="pwm-link" href={href}>{hashDisplay}</Link> : hashDisplay}
                  <span className="ml-3 text-pwm-muted font-sans">{describe(e)}</span>
                </div>
                {e.actor && (
                  <div className="text-xs text-slate-500 font-mono">by {shortAddr(e.actor)}</div>
                )}
              </div>
              <span className="text-xs text-pwm-muted whitespace-nowrap">{timeAgo(e.timestamp)}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
