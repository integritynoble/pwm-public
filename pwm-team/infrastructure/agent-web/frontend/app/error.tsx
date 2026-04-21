'use client';

import Link from 'next/link';
import { useEffect } from 'react';

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="pwm-card text-center py-12 max-w-xl mx-auto">
      <h1 className="text-2xl font-semibold">Something broke</h1>
      <p className="text-pwm-muted mt-2 text-sm">
        The page hit an error while rendering. This is usually transient —
        the API may be restarting or the indexer catching up.
      </p>
      {error.digest && (
        <p className="text-xs font-mono text-slate-500 mt-3">ref: {error.digest}</p>
      )}
      <div className="mt-5 flex justify-center gap-3 text-sm">
        <button onClick={() => reset()} className="pwm-link">Retry</button>
        <Link href="/" className="pwm-link">Home</Link>
      </div>
    </div>
  );
}
