import katex from 'katex';

/** Server-rendered KaTeX block — no client JS needed. */
export function Math({ tex, display = false }: { tex: string; display?: boolean }) {
  let html = '';
  try {
    html = katex.renderToString(tex, { displayMode: display, throwOnError: false, output: 'html' });
  } catch {
    html = `<code>${tex}</code>`;
  }
  return (
    <span
      className={display ? 'block overflow-x-auto py-2' : ''}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

/** Convert our plain-text forward models (e.g. "y = A x + n") into KaTeX. */
export function ForwardModel({ text }: { text: string | undefined | null }) {
  if (!text) return null;
  // Minimal ASCII-math -> LaTeX conversion. Good enough for display.
  const tex = text
    .replace(/sum_/g, '\\sum_')
    .replace(/lambda/g, '\\lambda')
    .replace(/sigma/g, '\\sigma')
    .replace(/sqrt\(/g, '\\sqrt{')
    .replace(/log10/g, '\\log_{10}')
    .replace(/log2/g, '\\log_2')
    .replace(/\*/g, '\\cdot ')
    .replace(/->/g, '\\to ');
  return <Math tex={tex} display />;
}
