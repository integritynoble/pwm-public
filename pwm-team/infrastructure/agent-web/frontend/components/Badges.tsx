export function GateBadge({ verdict }: { verdict: string }) {
  const v = verdict.toUpperCase();
  const cls =
    v === 'PASS' ? 'pwm-badge-pass' : v === 'FAIL' || v === 'INVALID' ? 'pwm-badge-fail' : 'pwm-badge-pending';
  return <span className={cls}>{v}</span>;
}

export function StatusBadge({ status }: { status: number }) {
  const labels: Record<number, [string, string]> = {
    0: ['Pending', 'pwm-badge-pending'],
    1: ['Challenged', 'pwm-badge-pending'],
    2: ['Finalized', 'pwm-badge-pass'],
    3: ['Invalid', 'pwm-badge-fail'],
    4: ['Resolved', 'pwm-badge-pass'],
  };
  const [label, cls] = labels[status] ?? ['Unknown', 'pwm-badge-pending'];
  return <span className={cls}>{label}</span>;
}
