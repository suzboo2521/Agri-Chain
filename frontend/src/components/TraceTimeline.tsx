import { useState } from "react";
import { Link } from "react-router-dom";
import { eventLabel, formatWhen, shortHash } from "../lib/format";
import type { HistoryItem } from "../lib/api";
import { cn } from "../lib/cn";

const ORDER = [
  "HARVEST",
  "QUALITY_CHECK",
  "TRANSPORT",
  "WAREHOUSE_ENTRY",
  "PROCESSING",
  "DISTRIBUTION",
  "RETAIL",
  "DOCUMENT",
];

export function TraceTimeline({
  batchId,
  history,
}: {
  batchId: string;
  history: HistoryItem[];
}) {
  const [open, setOpen] = useState<number | null>(null);
  const sorted = [...history].sort((a, b) => {
    const ia = ORDER.indexOf(a.transaction.event_type || "");
    const ib = ORDER.indexOf(b.transaction.event_type || "");
    if (ia !== ib && ia >= 0 && ib >= 0) return ia - ib;
    return a.block_index - b.block_index;
  });

  if (!sorted.length) {
    return (
      <p className="text-sm text-charcoal-600">
        No on-chain events yet for this batch.
      </p>
    );
  }

  return (
    <ol className="relative space-y-0 border-l-2 border-sage-200 pl-6">
      {sorted.map((item, i) => {
        const tx = item.transaction;
        const type = tx.event_type || "EVENT";
        const active = open === i;
        return (
          <li key={`${item.block_index}-${i}`} className="relative pb-8">
            <span
              className={cn(
                "absolute -left-[1.55rem] top-1 h-4 w-4 rounded-full border-2 border-cream-50",
                type === "DOCUMENT" ? "bg-gold-500" : "bg-emerald-600",
              )}
            />
            <button
              type="button"
              onClick={() => setOpen(active ? null : i)}
              className="w-full rounded-2xl bg-cream-50 p-4 text-left shadow-panel transition hover:bg-sage-50"
            >
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-gold-600">
                {eventLabel(type)}
              </p>
              <p className="mt-1 font-display text-lg text-forest-900">
                {tx.actor_id || "Unknown actor"}
              </p>
              <p className="text-sm text-charcoal-600">
                {tx.location || "—"} · {formatWhen(tx.timestamp || item.timestamp)}
              </p>
            </button>
            {active ? (
              <div className="mt-3 rounded-2xl border border-cream-200 bg-cream-50 p-4">
                <dl className="grid gap-3 text-sm sm:grid-cols-2">
                  <div>
                    <dt className="text-xs uppercase tracking-[0.14em] text-sage-700">Actor</dt>
                    <dd>{tx.actor_id || "—"}</dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-[0.14em] text-sage-700">Location</dt>
                    <dd>{tx.location || "—"}</dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-[0.14em] text-sage-700">Timestamp</dt>
                    <dd>{formatWhen(tx.timestamp || item.timestamp)}</dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-[0.14em] text-sage-700">Block</dt>
                    <dd>{item.block_index}</dd>
                  </div>
                </dl>
                <p className="hash mt-3 text-forest-800" title={item.block_hash}>
                  {shortHash(item.block_hash, 16)}
                </p>
                {tx.data && Object.keys(tx.data).length ? (
                  <pre className="mt-3 overflow-x-auto rounded-xl bg-sage-50 p-3 text-xs text-charcoal-700">
                    {JSON.stringify(tx.data, null, 2)}
                  </pre>
                ) : null}
                <Link
                  to={`/trace/${encodeURIComponent(batchId)}/${i}`}
                  className="mt-3 inline-block text-xs font-semibold uppercase tracking-[0.16em] text-forest-600"
                >
                  Open stage
                </Link>
              </div>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}
