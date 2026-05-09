import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { api } from '@/lib/api';
import { ForwardModel } from '@/components/Math';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const data = await api.spec(id);
  if (!data) return { title: `${id} not found · PWM Explorer` };
  const title = `${data.spec.title} (${data.spec.artifact_id}) · PWM Spec`;
  const description: string = data.spec?.six_tuple?.E?.forward?.slice(0, 200) ?? `PWM L2 spec ${id}`;
  return {
    title,
    description,
    openGraph: { title, description, siteName: 'PWM Explorer', type: 'website' },
    twitter: { card: 'summary', title, description },
  };
}

function tierBadge(tier: string | undefined) {
  if (tier === 'founder_vetted') {
    return <span className="pwm-pill !text-emerald-300 !border-emerald-500/40">★ Founder-vetted</span>;
  }
  if (tier === 'community_proposed') {
    return <span className="pwm-pill !text-cyan-300 !border-cyan-500/40">✓ Community-vetted</span>;
  }
  return <span className="pwm-pill !text-slate-400 !border-slate-600">📋 Stub — not mineable</span>;
}

export default async function SpecDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const data = await api.spec(id);
  if (!data) return notFound();

  const s = data.spec;
  const six = s.six_tuple ?? {};
  const protocol = s.protocol_fields ?? {};
  const tier = (s.registration_tier ?? 'stub') as string;

  return (
    <div className="space-y-8">
      <div>
        {data.parent_principle && (
          <Link href={`/principles/${data.parent_principle.artifact_id}`} className="pwm-link text-sm">
            ← {data.parent_principle.title} ({data.parent_principle.artifact_id})
          </Link>
        )}
        <h1 className="text-3xl font-bold tracking-tight mt-2">
          {s.title} <span className="text-pwm-muted text-lg">{s.artifact_id}</span>
        </h1>
        <div className="mt-2 flex flex-wrap gap-2 text-sm">
          {s.spec_type && <span className="pwm-pill">{s.spec_type}</span>}
          {typeof s.d_spec === 'number' && <span className="pwm-pill">d_spec = {s.d_spec}</span>}
          {tierBadge(tier)}
        </div>
      </div>

      {/* Six-tuple cards */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Six-tuple S = (Ω, E, B, I, O, ε)</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="pwm-card">
            <h3 className="text-sm font-semibold text-pwm-muted mb-2">Ω — parameter space</h3>
            {six.omega ? (
              <pre className="font-mono text-xs whitespace-pre-wrap bg-slate-950/60 p-2 rounded border border-slate-800 max-h-72 overflow-auto">
                {JSON.stringify(six.omega, null, 2)}
              </pre>
            ) : <p className="text-sm text-pwm-muted italic">not declared</p>}
          </div>
          <div className="pwm-card">
            <h3 className="text-sm font-semibold text-pwm-muted mb-2">E — forward operator</h3>
            {six.E?.forward && <ForwardModel text={six.E.forward} />}
            {six.E?.primitive_chain && (
              <div className="mt-3">
                <div className="text-xs text-pwm-muted mb-1">Primitive chain:</div>
                <code className="font-mono text-xs block bg-slate-950/60 p-2 rounded border border-slate-800">
                  {six.E.primitive_chain}
                </code>
              </div>
            )}
            {six.E?.inverse && (
              <p className="text-sm text-pwm-muted italic mt-3">Inverse: {six.E.inverse}</p>
            )}
          </div>
          <div className="pwm-card">
            <h3 className="text-sm font-semibold text-pwm-muted mb-2">B — boundary constraints</h3>
            {six.B ? (
              <ul className="text-sm space-y-1">
                {Object.entries(six.B).map(([k, v]) => (
                  <li key={k}>
                    <span className="text-pwm-muted">{k}:</span> <span className="font-mono">{String(v)}</span>
                  </li>
                ))}
              </ul>
            ) : <p className="text-sm text-pwm-muted italic">not declared</p>}
          </div>
          <div className="pwm-card">
            <h3 className="text-sm font-semibold text-pwm-muted mb-2">I — initialization</h3>
            <p className="font-mono text-sm">{six.I?.strategy ?? '—'}</p>
          </div>
          <div className="pwm-card">
            <h3 className="text-sm font-semibold text-pwm-muted mb-2">O — observable outputs</h3>
            {Array.isArray(six.O) && six.O.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {six.O.map((o: string) => (
                  <span key={o} className="pwm-pill">{o}</span>
                ))}
              </div>
            ) : <p className="text-sm text-pwm-muted italic">none</p>}
          </div>
          <div className="pwm-card">
            <h3 className="text-sm font-semibold text-pwm-muted mb-2">ε — acceptance threshold</h3>
            {six.epsilon_fn ? (
              <code className="font-mono text-xs block bg-slate-950/60 p-2 rounded border border-slate-800 break-words">
                {six.epsilon_fn}
              </code>
            ) : <p className="text-sm text-pwm-muted italic">not declared</p>}
          </div>
        </div>
      </section>

      {/* Protocol fields (input/output formats + baselines) */}
      {(protocol.input_format || protocol.output_format || protocol.baselines) && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Protocol fields</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {protocol.input_format && (
              <div className="pwm-card">
                <h3 className="text-sm font-semibold text-pwm-muted mb-2">Input format</h3>
                <pre className="font-mono text-xs whitespace-pre-wrap bg-slate-950/60 p-2 rounded border border-slate-800">
                  {JSON.stringify(protocol.input_format, null, 2)}
                </pre>
              </div>
            )}
            {protocol.output_format && (
              <div className="pwm-card">
                <h3 className="text-sm font-semibold text-pwm-muted mb-2">Output format</h3>
                <pre className="font-mono text-xs whitespace-pre-wrap bg-slate-950/60 p-2 rounded border border-slate-800">
                  {JSON.stringify(protocol.output_format, null, 2)}
                </pre>
              </div>
            )}
            {Array.isArray(protocol.baselines) && protocol.baselines.length > 0 && (
              <div className="pwm-card md:col-span-2">
                <h3 className="text-sm font-semibold text-pwm-muted mb-2">Authored baselines</h3>
                <table className="pwm-table text-sm">
                  <thead>
                    <tr><th>Solver</th><th>Method sig</th><th>Expected metric</th></tr>
                  </thead>
                  <tbody>
                    {protocol.baselines.map((b: any) => (
                      <tr key={b.name}>
                        <td>{b.name}</td>
                        <td className="font-mono">{b.method_sig ?? '—'}</td>
                        <td>
                          {Object.entries(b)
                            .filter(([k]) => k !== 'name' && k !== 'method_sig')
                            .map(([k, v]) => `${k}=${v}`)
                            .join(', ')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Child benchmarks */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Child benchmarks ({data.child_benchmarks.length})</h2>
        {data.child_benchmarks.length === 0 ? (
          <div className="pwm-card text-pwm-muted italic">
            No L3 benchmarks registered under this spec yet.
          </div>
        ) : (
          <div className="pwm-card overflow-x-auto">
            <table className="pwm-table">
              <thead>
                <tr><th>Title</th><th>ID</th><th>ρ</th><th>Domain</th></tr>
              </thead>
              <tbody>
                {data.child_benchmarks.map((b) => (
                  <tr key={b.artifact_id}>
                    <td>
                      <Link className="pwm-link" href={`/benchmarks/${b.artifact_id}`}>
                        {b.title || b.artifact_id}
                      </Link>
                    </td>
                    <td className="font-mono">{b.artifact_id}</td>
                    <td>{b.rho ?? '—'}</td>
                    <td>{b.domain ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Sibling specs */}
      {data.siblings.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Other specs under the same Principle ({data.siblings.length})</h2>
          <div className="pwm-card overflow-x-auto">
            <table className="pwm-table">
              <thead>
                <tr><th>Title</th><th>ID</th><th>Type</th><th>d_spec</th></tr>
              </thead>
              <tbody>
                {data.siblings.map((sib) => (
                  <tr key={sib.artifact_id}>
                    <td>
                      <Link className="pwm-link" href={`/specs/${sib.artifact_id}`}>
                        {sib.title}
                      </Link>
                    </td>
                    <td className="font-mono">{sib.artifact_id}</td>
                    <td>{sib.spec_type}</td>
                    <td>{sib.d_spec ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
