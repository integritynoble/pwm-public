import Link from 'next/link';
import { api, type MatchCandidate } from '@/lib/api';
import { ApiDown } from '@/components/Empty';

export const dynamic = 'force-dynamic';

type SP = {
  prompt?: string;
  domain?: string;
  modality?: string;
  h?: string;
  w?: string;
  noise?: string;
};

export default async function MatchPage({
  searchParams,
}: {
  searchParams: Promise<SP>;
}) {
  const params = await searchParams;
  const hasQuery = !!(params.prompt || params.domain || params.modality ||
                      params.h || params.w || params.noise);

  const result = hasQuery
    ? await api.match({
        prompt: params.prompt,
        domain: params.domain,
        modality: params.modality,
        h: params.h ? Number(params.h) : undefined,
        w: params.w ? Number(params.w) : undefined,
        noise: params.noise ? Number(params.noise) : undefined,
      })
    : null;

  if (hasQuery && !result) return <ApiDown />;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Match your data</h1>
        <p className="text-sm text-pwm-muted mt-2 max-w-2xl">
          Describe what you have, and PWM finds the benchmarks whose Ω (domain
          of valid operation) covers your case. This is the{' '}
          <strong>faceted floor</strong> — deterministic keyword + filter
          matching, no LLM. Natural-language matching is a third-party bounty
          (<Link href="/bounties" className="pwm-link">Bounty #8</Link>).
        </p>
      </div>

      <form method="GET" action="/match" className="space-y-4 pwm-card max-w-3xl">
        <div>
          <label className="block text-sm font-medium mb-1">
            Free-text prompt
          </label>
          <textarea
            name="prompt"
            defaultValue={params.prompt ?? ''}
            placeholder="e.g. &quot;I have a CASSI snapshot, 256×256, mild calibration drift, noise ~2%, need a hyperspectral cube out&quot;"
            rows={3}
            className="w-full rounded bg-slate-900/60 border border-slate-700 px-3 py-2 text-sm"
          />
        </div>

        <details className="text-sm">
          <summary className="cursor-pointer text-pwm-muted">
            Optional structured filters
          </summary>
          <div className="grid grid-cols-2 gap-3 mt-3">
            <div>
              <label className="block text-xs uppercase tracking-wide text-pwm-muted mb-1">
                Domain
              </label>
              <input
                name="domain"
                defaultValue={params.domain ?? ''}
                placeholder="imaging"
                className="w-full rounded bg-slate-900/60 border border-slate-700 px-3 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-wide text-pwm-muted mb-1">
                Modality
              </label>
              <input
                name="modality"
                defaultValue={params.modality ?? ''}
                placeholder="snapshot"
                className="w-full rounded bg-slate-900/60 border border-slate-700 px-3 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-wide text-pwm-muted mb-1">
                Height (H)
              </label>
              <input
                name="h"
                type="number"
                defaultValue={params.h ?? ''}
                placeholder="256"
                className="w-full rounded bg-slate-900/60 border border-slate-700 px-3 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-wide text-pwm-muted mb-1">
                Width (W)
              </label>
              <input
                name="w"
                type="number"
                defaultValue={params.w ?? ''}
                placeholder="256"
                className="w-full rounded bg-slate-900/60 border border-slate-700 px-3 py-1.5 text-sm"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-xs uppercase tracking-wide text-pwm-muted mb-1">
                Max noise level you need the benchmark to tolerate
              </label>
              <input
                name="noise"
                type="number"
                step="0.01"
                min="0"
                max="1"
                defaultValue={params.noise ?? ''}
                placeholder="0.05"
                className="w-full rounded bg-slate-900/60 border border-slate-700 px-3 py-1.5 text-sm"
              />
            </div>
          </div>
        </details>

        <div className="flex items-center gap-3">
          <button
            type="submit"
            className="px-4 py-2 rounded bg-gradient-to-r from-cyan-500 to-indigo-500 text-black font-semibold text-sm"
          >
            Match
          </button>
          {hasQuery && (
            <Link href="/match" className="text-sm text-pwm-muted hover:text-pwm-accent">
              Reset
            </Link>
          )}
        </div>
      </form>

      {result && (
        <section className="space-y-4">
          {result.confidence_floor_hit ? (
            <div className="pwm-card max-w-3xl border-amber-500/40">
              <div className="text-amber-400 text-sm font-semibold mb-2">
                No confident match
              </div>
              {result.clarifying_question && (
                <p className="text-sm">{result.clarifying_question}</p>
              )}
              <p className="text-xs text-pwm-muted mt-3">
                If no benchmark covers your case, PWM's{' '}
                <Link href="/bounties" className="pwm-link">
                  translator marketplace
                </Link>{' '}
                lets third parties author a new one. You fund a bounty; a
                translator stakes on delivery.
              </p>
            </div>
          ) : (
            <>
              <h2 className="text-xl font-semibold">
                Top {result.candidates.length} candidate{result.candidates.length === 1 ? '' : 's'}
              </h2>
              <div className="space-y-3 max-w-3xl">
                {result.candidates.map((c) => <MatchCandidateCard key={c.benchmark_id} c={c} />)}
              </div>
              {result.clarifying_question && (
                <div className="pwm-card max-w-3xl border-cyan-500/30">
                  <div className="text-cyan-400 text-sm font-semibold mb-1">
                    Need more detail?
                  </div>
                  <p className="text-sm">{result.clarifying_question}</p>
                </div>
              )}
            </>
          )}
        </section>
      )}

      <footer className="text-xs text-pwm-muted max-w-3xl pt-4 border-t border-slate-800">
        Reference matcher — deterministic keyword + filter scoring, no LLM, no
        external API. Source:{' '}
        <code className="text-slate-400">pwm-team/infrastructure/agent-web/api/matching.py</code>{' '}
        (web) and{' '}
        <code className="text-slate-400">pwm-team/infrastructure/agent-cli/pwm_node/commands/match.py</code>{' '}
        (CLI). Third-party LLM-routed matchers compete via{' '}
        <Link href="/bounties" className="pwm-link">Bounty #8</Link> once qualified.
      </footer>
    </div>
  );
}


function matchBandLabel(band: MatchCandidate['score_band'] | undefined, score: number) {
  // Fallback: derive from raw score if API didn't return a band
  const b = band ?? (score >= 3.0 ? 'strong' : score >= 2.0 ? 'weak' : 'none');
  if (b === 'strong')
    return { text: 'Strong match', stars: '★★★★', color: 'text-emerald-400 border-emerald-500/40' };
  if (b === 'weak')
    return { text: 'Weak match', stars: '★★', color: 'text-amber-400 border-amber-500/40' };
  return { text: 'No match', stars: '☆', color: 'text-slate-500 border-slate-700' };
}


function MatchCandidateCard({ c }: { c: MatchCandidate }) {
  const band = matchBandLabel(c.score_band, c.score);
  return (
    <div className={`pwm-card ${band.color.split(' ')[1] ?? ''}`.trim() + ' border'}>
      <div className="flex items-start gap-4 flex-wrap">
        {c.preview_urls && (
          <div className="flex gap-1 shrink-0">
            <img
              src={c.preview_urls.snapshot}
              alt={`${c.benchmark_id} snapshot`}
              className="w-24 h-24 border border-slate-800 rounded bg-slate-950 [image-rendering:pixelated]"
              loading="lazy"
            />
            <img
              src={c.preview_urls.ground_truth}
              alt={`${c.benchmark_id} ground truth`}
              className="w-24 h-24 border border-slate-800 rounded bg-slate-950 [image-rendering:pixelated]"
              loading="lazy"
            />
          </div>
        )}
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-pwm-muted">#{c.rank}</span>
            <span className="font-mono font-semibold text-pwm-accent">{c.benchmark_id}</span>
            {c.tier && <span className="pwm-pill">tier: {c.tier}</span>}
            <span className={`text-xs font-semibold ${band.color.split(' ')[0]}`}>
              {band.stars} {band.text}
            </span>
            <span className="text-xs text-pwm-muted ml-auto">score {c.score.toFixed(2)}</span>
          </div>
          <p className="text-sm break-words">{c.rationale}</p>
          <div className="flex gap-2 pt-1">
            <Link
              href={`/benchmarks/${c.benchmark_id}`}
              className="inline-block px-3 py-1.5 rounded bg-gradient-to-r from-cyan-500 to-indigo-500 text-black font-semibold text-sm"
            >
              Try this benchmark →
            </Link>
            <Link
              href={`/bounties`}
              className="inline-block px-3 py-1.5 rounded border border-slate-700 text-sm text-pwm-muted hover:text-pwm-accent hover:border-pwm-accent"
            >
              Compete (bounty)
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
