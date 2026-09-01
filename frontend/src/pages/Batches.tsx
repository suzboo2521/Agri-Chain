import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getBatches, type BatchRecord } from "../lib/api";
import { friendlyError, formatKg } from "../lib/format";
import { EmptyState, LoadingLabel, PageHeader, Panel } from "../components/ui";
import { cn } from "../lib/cn";

export function BatchesPage() {
  const [rows, setRows] = useState<BatchRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getBatches();
      setRows(res.batches);
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div>
      <PageHeader
        kicker="Directory"
        title="Registered batches"
        subtitle="Every harvest recorded on the AgriChain ledger."
        backTo="/"
      />
      {loading ? <LoadingLabel>Loading batches</LoadingLabel> : null}
      {error ? (
        <EmptyState title="Could not load batches" message={error} onRetry={() => void load()} />
      ) : null}
      {!loading && !error && rows.length === 0 ? (
        <EmptyState
          title="No batches yet"
          message="Register a harvest to create the first on-chain batch."
        />
      ) : null}
      <div className="grid gap-3">
        {rows.map((b) => (
          <Link key={b.batch_id} to={`/batches/${encodeURIComponent(b.batch_id)}`}>
            <Panel className="flex flex-wrap items-center justify-between gap-3 transition hover:border-gold-400">
              <div>
                <p className="font-mono text-sm text-forest-900">{b.batch_id}</p>
                <p className="text-sm text-charcoal-600">
                  {b.crop} · {b.farmer} · {b.location} · {formatKg(b.quantity_kg)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {b.has_alert ? (
                  <span className="rounded-full bg-alert-soft px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-alert">
                    Anomaly
                  </span>
                ) : null}
                <span
                  className={cn(
                    "rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em]",
                    "bg-sage-100 text-forest-800",
                  )}
                >
                  {b.status}
                </span>
              </div>
            </Panel>
          </Link>
        ))}
      </div>
    </div>
  );
}
