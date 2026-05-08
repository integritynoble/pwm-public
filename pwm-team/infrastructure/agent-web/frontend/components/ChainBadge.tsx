import { api } from '@/lib/api';

/**
 * ChainBadge — yellow TESTNET / blue MAINNET pill in the global header.
 *
 * Closes Gap 1 from PWM_CROSS_CHAIN_UX_DESIGN_2026-05-08.md § 3:
 * a user landing on /cert/0xabc… or /benchmarks/L3-003 needs to
 * immediately see whether they're on real-money infra or on testnet.
 *
 * Reads from /api/network (which already exists; resolved via
 * PWM_NETWORK env var on the server). Server-side fetch — no client
 * JS needed.
 *
 * Failure mode: if /api/network is unreachable, the badge falls back
 * to "UNKNOWN" rather than blocking the layout render.
 */
export async function ChainBadge() {
  let network: string;
  let chainId: number | string | null = null;
  try {
    const data = await api.network();
    if (data) {
      network = data.network;
      // addresses.chainId is set by the backend per-network.
      const addrs = data.addresses as { chainId?: number } | undefined;
      chainId = addrs?.chainId ?? null;
    } else {
      network = 'unknown';
    }
  } catch {
    network = 'unknown';
  }

  const isMainnet = network === 'mainnet';
  const isTestnet = network === 'testnet';

  // Tailwind colour classes: yellow for testnet (caution: fake money),
  // blue for mainnet (production), grey for unknown / offline.
  const cls = isMainnet
    ? 'bg-blue-500/15 text-blue-300 border border-blue-500/40'
    : isTestnet
      ? 'bg-yellow-500/15 text-yellow-300 border border-yellow-500/40'
      : 'bg-slate-700/30 text-slate-400 border border-slate-700/60';

  const label = isMainnet
    ? 'MAINNET'
    : isTestnet
      ? 'TESTNET'
      : network.toUpperCase();

  // Tooltip with chain context (so a power user can confirm chainId)
  const tip = isMainnet
    ? `Base mainnet (chainId ${chainId ?? '?'}) — real PWM, real ETH. Hardware-wallet recommended.`
    : isTestnet
      ? `Sepolia testnet (chainId ${chainId ?? '?'}) — faucet ETH, fake PWM. Safe to experiment.`
      : 'Network unknown — backend /api/network unreachable or PWM_NETWORK unset.';

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wide ${cls}`}
      title={tip}
      aria-label={`PWM network: ${label}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
      {label}
    </span>
  );
}
