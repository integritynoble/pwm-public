import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'PWM Web Explorer',
  description:
    'Public explorer for the Physics World Model protocol — principles, benchmarks, certificates, pools.',
};

const NAV = [
  { href: '/', label: 'Overview' },
  { href: '/match', label: 'Match' },
  { href: '/demos', label: 'Demos' },
  { href: '/principles', label: 'Principles' },
  { href: '/benchmarks', label: 'Benchmarks' },
  { href: '/pools', label: 'Pools' },
  { href: '/bounties', label: 'Bounties' },
  { href: '/contribute', label: 'Contribute' },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-slate-800 bg-slate-950/70 backdrop-blur sticky top-0 z-10">
          <div className="max-w-6xl mx-auto px-4 py-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-400 to-indigo-500 flex items-center justify-center text-black font-black">
                P
              </div>
              <span className="font-semibold tracking-tight">PWM Explorer</span>
              <span className="pwm-pill ml-2">reference impl</span>
            </Link>
            <nav className="flex flex-wrap gap-4 text-sm">
              {NAV.map((n) => (
                <Link key={n.href} href={n.href} className="hover:text-pwm-accent">
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-4 py-8">{children}</main>
        <footer className="max-w-6xl mx-auto px-4 py-8 text-xs text-slate-500 border-t border-slate-900 mt-12">
          <p>
            PWM Explorer — read-only view of the Physics World Model protocol on Sepolia testnet.
            Bounty reference implementation (80,000 PWM). Works without MetaMask; all transactions
            go through pwm-node.
          </p>
        </footer>
      </body>
    </html>
  );
}
