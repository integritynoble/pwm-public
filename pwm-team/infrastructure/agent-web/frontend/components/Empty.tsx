export function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div className="pwm-card text-center text-pwm-muted italic py-10">
      {children}
    </div>
  );
}

export function ApiDown() {
  return (
    <Empty>
      API unreachable. Is the indexer/API running? Set <code>PWM_API_URL</code>.
    </Empty>
  );
}
