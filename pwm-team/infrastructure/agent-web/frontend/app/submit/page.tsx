import Link from 'next/link';

export default function SubmitPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-3xl font-bold tracking-tight">Submit a solution</h1>
      <p className="text-pwm-muted">
        The web explorer is read-only. Submitting L2/L3 artifacts or certificates requires the
        <code className="mx-1 px-1 bg-slate-900/60 border border-slate-800 rounded">pwm-node</code>
        CLI, which signs transactions with your wallet and writes directly to the contracts.
      </p>

      <ol className="pwm-card space-y-3 text-sm">
        <li>
          <strong>1. Install pwm-node.</strong>{' '}
          <code className="font-mono">npm install -g @pwm/node</code> (once published)
        </li>
        <li>
          <strong>2. Configure endpoint.</strong> Point at Sepolia testnet RPC and provide
          your keystore:{' '}
          <code className="font-mono">pwm-node config set rpc https://rpc.sepolia.org</code>
        </li>
        <li>
          <strong>3. Pick a benchmark.</strong> Browse{' '}
          <Link href="/benchmarks" className="pwm-link">/benchmarks</Link>{' '}
          and copy the hash.
        </li>
        <li>
          <strong>4. Run your solver</strong> locally to produce artifacts; then
          <code className="font-mono mx-1">pwm-node submit &lt;benchmark&gt; --cert path/to/cert.json</code>
        </li>
        <li>
          <strong>5. Track your submission</strong> under{' '}
          <Link href="/benchmarks" className="pwm-link">/benchmarks/&lt;id&gt;</Link>
          {' '}(within ≤5 minutes of the tx being mined).
        </li>
      </ol>

      <p className="text-xs text-pwm-muted">
        The explorer never asks for a private key; if a page prompts you to sign anything, close it.
      </p>
    </div>
  );
}
