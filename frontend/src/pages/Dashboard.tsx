import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getActivity, getBatches, getStats, type ActivityResponse, type BatchesResponse, type StatsResponse } from "../lib/api";
import { friendlyError, eventLabel, formatWhen } from "../lib/format";
import { AnimatedCounter } from "../components/AnimatedCounter";
import { EmptyState, LoadingLabel, Panel } from "../components/ui";
import { JourneyActions, JourneyLine } from "../components/Journey";

export function DashboardPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [activity, setActivity] = useState<ActivityResponse | null>(null);
  const [batches, setBatches] = useState<BatchesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, a, b] = await Promise.all([getStats(), getActivity(12), getBatches()]);
      setStats(s);
      setActivity(a);
      setBatches(b);
    } catch (e) {
      setError(friendlyError(e));
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div>
      <section className="relative mb-8 overflow-hidden rounded-organ">
        <img
          src="/images/rice-field.jpg"
          alt="Rice paddies"
          className="h-56 w-full object-cover md:h-72"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-forest-950/85 via-forest-950/45 to-transparent" />
        <div className="absolute inset-0 flex flex-col justify-end p-6 md:p-10">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold-400">
            Live operations
          </p>
          <h1 className="mt-2 font-display text-4xl text-cream-50 md:text-5xl">
            From farm to consumer
          </h1>
          <p className="mt-2 max-w-lg text-sm text-cream-100/90">
            Every batch on this ledger is mined, hashed, and ready to verify.
          </p>
        </div>
      </section>

      {loading ? <LoadingLabel>Loading dashboard</LoadingLabel> : null}
      {error ? (
        <EmptyState
          title="Dashboard unavailable"
          message={error}
          onRetry={() => void load()}
        />
      ) : null}

      {stats && !error ? (
        <div className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Batches" value={stats.total_batches} />
          <StatCard label="Verified" value={stats.verified} />
          <StatCard label="Blocks" value={stats.total_blocks} />
          <StatCard
            label="High risk"
            value={stats.high_risk}
            alert={stats.high_risk > 0}
          />
        </div>
      ) : null}

      <Panel className="mb-8">
        <p className="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-gold-600">
          Farm → Consumer
        </p>
        <JourneyLine />
      </Panel>

      <h2 className="mb-3 font-display text-2xl text-forest-900">Action modules</h2>
      <JourneyActions />

      <div className="mt-8 grid gap-6 lg:grid-cols-5">
        <Panel className="lg:col-span-3">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-xl text-forest-900">Recent activity</h2>
            <Link
              to="/analytics"
              className="text-xs font-semibold uppercase tracking-[0.16em] text-forest-600"
            >
              Analytics
            </Link>
          </div>
          {!activity?.events.length ? (
            <p className="text-sm text-charcoal-600">No events yet. Register a batch to begin.</p>
          ) : (
            <ul className="space-y-3">
              {activity.events.map((ev) => (
                <li key={ev.id} className="flex items-start justify-between gap-3 border-b border-cream-200 pb-3 last:border-0">
                  <div>
                    <p className="text-sm font-semibold text-forest-900">
                      {eventLabel(ev.event_type)}
                    </p>
                    <p className="text-xs text-charcoal-600">
                      {ev.batch_id} · {ev.actor_id} · {ev.location || "—"}
                    </p>
                  </div>
                  <p className="shrink-0 text-xs text-sage-700">{formatWhen(ev.timestamp)}</p>
                </li>
              ))}
            </ul>
          )}
        </Panel>
        <Panel className="lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-xl text-forest-900">Batches</h2>
            <Link
              to="/batches"
              className="text-xs font-semibold uppercase tracking-[0.16em] text-forest-600"
            >
              Directory
            </Link>
          </div>
          {!batches?.batches.length ? (
            <p className="text-sm text-charcoal-600">No registered batches.</p>
          ) : (
            <ul className="space-y-2">
              {batches.batches.slice(0, 8).map((b) => (
                <li key={b.batch_id}>
                  <Link
                    to={`/batches/${encodeURIComponent(b.batch_id)}`}
                    className="block rounded-2xl px-3 py-2 hover:bg-sage-50"
                  >
                    <p className="font-mono text-sm text-forest-900">{b.batch_id}</p>
                    <p className="text-xs text-charcoal-600">
                      {b.crop} · {b.location}
                    </p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  alert,
}: {
  label: string;
  value: number;
  alert?: boolean;
}) {
  return (
    <div className="glass rounded-organ p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sage-700">
        {label}
      </p>
      <p
        className={
          alert
            ? "mt-2 font-display text-4xl text-alert"
            : "mt-2 font-display text-4xl text-forest-900"
        }
      >
        <AnimatedCounter value={value} />
      </p>
    </div>
  );
}
