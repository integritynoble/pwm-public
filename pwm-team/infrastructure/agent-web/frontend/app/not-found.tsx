import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="pwm-card text-center py-16 max-w-xl mx-auto">
      <div className="text-6xl font-black tracking-tight bg-gradient-to-r from-cyan-300 to-indigo-400 bg-clip-text text-transparent">
        404
      </div>
      <h1 className="text-2xl font-semibold mt-3">Not in the index</h1>
      <p className="text-pwm-muted mt-2 max-w-md mx-auto text-sm">
        The hash, principle, or benchmark you&apos;re looking for isn&apos;t on-chain
        or isn&apos;t in our genesis catalogue yet. If it was just registered,
        the indexer catches up within ~12s.
      </p>
      <div className="mt-6 flex justify-center gap-3 text-sm">
        <Link href="/" className="pwm-link">Overview</Link>
        <Link href="/principles" className="pwm-link">Principles</Link>
        <Link href="/benchmarks" className="pwm-link">Benchmarks</Link>
      </div>
    </div>
  );
}
