/** Formatting helpers shared by pages. */

export function shortAddr(addr: string | null | undefined, len = 6): string {
  if (!addr) return '—';
  if (addr.length <= len * 2 + 2) return addr;
  return `${addr.slice(0, len + 2)}…${addr.slice(-len)}`;
}

export function weiToPwm(wei: string | null | undefined, decimals = 4): string {
  if (!wei) return '0';
  try {
    const big = BigInt(wei);
    const whole = big / 10n ** 18n;
    const frac = big % 10n ** 18n;
    const fracStr = frac.toString().padStart(18, '0').slice(0, decimals).replace(/0+$/, '');
    return fracStr ? `${whole}.${fracStr}` : whole.toString();
  } catch {
    return '0';
  }
}

export function timeAgo(unix: number | undefined | null): string {
  if (!unix) return '—';
  const now = Math.floor(Date.now() / 1000);
  const diff = Math.max(0, now - unix);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export function formatNumber(n: number | string | undefined): string {
  if (n == null) return '—';
  const num = typeof n === 'string' ? Number(n) : n;
  if (!isFinite(num)) return String(n);
  return num.toLocaleString();
}

export const STATUS_LABELS: Record<number, string> = {
  0: 'Pending',
  1: 'Challenged',
  2: 'Finalized',
  3: 'Invalid',
  4: 'Resolved',
};
