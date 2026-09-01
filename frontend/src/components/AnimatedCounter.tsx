import { useEffect, useRef, useState } from "react";

export function AnimatedCounter({
  value,
  className,
}: {
  value: number;
  className?: string;
}) {
  const [shown, setShown] = useState(0);
  const from = useRef(0);

  useEffect(() => {
    const start = from.current;
    const end = value;
    const t0 = performance.now();
    const dur = 700;
    let raf = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - t0) / dur);
      const eased = 1 - (1 - p) ** 3;
      const next = start + (end - start) * eased;
      setShown(end % 1 === 0 ? Math.round(next) : Math.round(next * 10) / 10);
      if (p < 1) raf = requestAnimationFrame(tick);
      else from.current = end;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value]);

  return (
    <span className={className}>
      {shown.toLocaleString(undefined, { maximumFractionDigits: 1 })}
    </span>
  );
}
