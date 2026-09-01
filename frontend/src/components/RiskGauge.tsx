import { cn } from "../lib/cn";

export function RiskGauge({
  score,
  level,
}: {
  score: number;
  level: string;
}) {
  const high = level.toUpperCase() === "HIGH";
  const med = level.toUpperCase() === "MEDIUM";
  const color = high ? "#b42318" : med ? "#a88840" : "#2a8a5c";
  const r = 54;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.min(100, Math.max(0, score)) / 100) * c;

  return (
    <div className="relative mx-auto h-44 w-44">
      <svg viewBox="0 0 140 140" className="h-full w-full -rotate-90" aria-hidden>
        <circle cx="70" cy="70" r={r} fill="none" stroke="#efe8d4" strokeWidth="12" />
        <circle
          cx="70"
          cy="70"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-4xl text-forest-900">{score}</span>
        <span
          className={cn(
            "text-xs font-semibold uppercase tracking-[0.2em]",
            high ? "text-alert" : med ? "text-gold-600" : "text-emerald-700",
          )}
        >
          {level}
        </span>
      </div>
    </div>
  );
}
