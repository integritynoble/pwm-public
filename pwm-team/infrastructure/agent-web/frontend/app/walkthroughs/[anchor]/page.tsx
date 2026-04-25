import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const ALLOWED = new Set(['cassi', 'cacti']);

const ANCHOR_TITLE: Record<string, string> = {
  cassi: 'CASSI — Coded Aperture Snapshot Spectral Imaging',
  cacti: 'CACTI — Coded Aperture Compressive Temporal Imaging',
};

const ANCHOR_TO_BENCHMARK: Record<string, string> = {
  cassi: 'L3-003',
  cacti: 'L3-004',
};

const ANCHOR_TO_PRINCIPLE: Record<string, string> = {
  cassi: 'L1-003',
  cacti: 'L1-004',
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ anchor: string }>;
}): Promise<Metadata> {
  const { anchor } = await params;
  const title = ANCHOR_TITLE[anchor] ?? anchor;
  return { title: `${title} · Walkthrough · PWM` };
}

async function loadWalkthrough(anchor: string): Promise<string | null> {
  const base = process.env.PWM_API_URL || 'http://localhost:8000';
  const res = await fetch(`${base}/api/walkthrough/${anchor}`, {
    next: { revalidate: 300 },
  });
  if (!res.ok) return null;
  return res.text();
}

export default async function WalkthroughPage({
  params,
}: {
  params: Promise<{ anchor: string }>;
}) {
  const { anchor } = await params;
  if (!ALLOWED.has(anchor)) return notFound();

  const md = await loadWalkthrough(anchor);
  if (md === null) return notFound();

  const principleId = ANCHOR_TO_PRINCIPLE[anchor];
  const benchmarkId = ANCHOR_TO_BENCHMARK[anchor];
  const title = ANCHOR_TITLE[anchor];

  return (
    <div className="space-y-6">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div>
          <Link href="/principles" className="pwm-link text-sm">
            ← All principles
          </Link>
          <h1 className="text-3xl font-bold tracking-tight mt-2">{title}</h1>
          <p className="text-sm text-pwm-muted mt-1">
            Complete four-layer walkthrough — domain expert seeds → S1-S4 →
            Principle → spec.md → Benchmark → Solution.
          </p>
        </div>
        <div className="flex gap-2 text-sm">
          <Link
            href={`/principles/${principleId}`}
            className="px-3 py-1.5 rounded border border-slate-700 hover:border-pwm-accent hover:text-pwm-accent"
          >
            Principle {principleId}
          </Link>
          <Link
            href={`/benchmarks/${benchmarkId}`}
            className="px-3 py-1.5 rounded bg-gradient-to-r from-cyan-500 to-indigo-500 text-black font-semibold"
          >
            Benchmark {benchmarkId} →
          </Link>
        </div>
      </div>

      <article
        className={[
          'prose prose-invert max-w-none',
          'prose-headings:tracking-tight',
          'prose-h1:text-2xl prose-h2:text-xl prose-h3:text-base',
          'prose-code:text-pwm-accent prose-code:bg-slate-900/60 prose-code:px-1 prose-code:py-0.5 prose-code:rounded',
          'prose-pre:bg-slate-950 prose-pre:border prose-pre:border-slate-800',
          'prose-a:text-pwm-accent prose-a:no-underline hover:prose-a:underline',
          'prose-strong:text-white',
          'prose-table:text-sm',
        ].join(' ')}
      >
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
      </article>

      <footer className="text-xs text-pwm-muted pt-6 border-t border-slate-800">
        Source:{' '}
        <code className="text-slate-400">
          papers/Proof-of-Solution/mine_example/{anchor}.md
        </code>
        . Mirrored to{' '}
        <code className="text-slate-400">
          pwm-team/pwm_product/walkthroughs/{anchor}.md
        </code>{' '}
        and served at <code className="text-slate-400">/api/walkthrough/{anchor}</code>.
      </footer>
    </div>
  );
}
