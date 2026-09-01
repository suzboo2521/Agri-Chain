import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getActivity, getAnalytics, getStats, type ActivityResponse, type AnalyticsResponse, type StatsResponse } from "../lib/api";
import { eventLabel, formatWhen, friendlyError } from "../lib/format";
import { AnimatedCounter } from "../components/AnimatedCounter";
import { EmptyState, LoadingLabel, PageHeader, Panel } from "../components/ui";

const SAGE = ["#1f6b48", "#5c7a5c", "#a88840", "#7a8b3e", "#2d5c46", "#8aa88a"];

export function AnalyticsPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [activity, setActivity] = useState<ActivityResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, a, act] = await Promise.all([getStats(), getAnalytics(), getActivity(30)]);
      setStats(s);
      setAnalytics(a);
      setActivity(act);
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const crops = useMemo(
    () =>
      Object.entries(analytics?.crop_mix || {}).map(([name, value]) => ({ name, value })),
    [analytics],
  );
  const events = useMemo(
    () =>
      Object.entries(analytics?.event_mix || {}).map(([name, value]) => ({
        name: eventLabel(name),
        value,
      })),
    [analytics],
  );

  return (
    <div>
      <PageHeader
        kicker="Command centre"
        title="Analytics"
        subtitle="Aggregates from GET /analytics and GET /stats. Activity is GET /activity."
        backTo="/"
      />
      {loading ? <LoadingLabel>Loading analytics</LoadingLabel> : null}
      {error ? (
        <EmptyState title="Analytics unavailable" message={error} onRetry={() => void load()} />
      ) : null}
      {stats ? (
        <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Mini label="Batches" value={stats.total_batches} />
          <Mini label="Blocks" value={stats.total_blocks} />
          <Mini label="Quality failures" value={stats.quality_failures} alert={stats.quality_failures > 0} />
          <Mini label="Temp alerts" value={stats.temperature_alerts} alert={stats.temperature_alerts > 0} />
        </div>
      ) : null}
      {analytics ? (
        <div className="mb-6 grid gap-6 lg:grid-cols-2">
          <Panel className="h-72">
            <h2 className="mb-3 font-display text-xl text-forest-900">Crop mix</h2>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={crops} dataKey="value" nameKey="name" innerRadius={48} outerRadius={80}>
                  {crops.map((_, i) => (
                    <Cell key={i} fill={SAGE[i % SAGE.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Panel>
          <Panel className="h-72">
            <h2 className="mb-3 font-display text-xl text-forest-900">Event mix</h2>
            <ResponsiveContainer>
              <BarChart data={events}>
                <CartesianGrid stroke="#efe8d4" />
                <XAxis dataKey="name" hide />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#1f6b48" radius={8} />
              </BarChart>
            </ResponsiveContainer>
          </Panel>
        </div>
      ) : null}
      <Panel>
        <h2 className="mb-4 font-display text-xl text-forest-900">Activity timeline</h2>
        {!activity?.events.length ? (
          <p className="text-sm text-charcoal-600">No events yet.</p>
        ) : (
          <ol className="space-y-4 border-l-2 border-sage-200 pl-5">
            {activity.events.map((ev) => (
              <li key={ev.id} className="relative">
                <span className="absolute -left-[1.4rem] top-1.5 h-3 w-3 rounded-full bg-emerald-600" />
                <p className="text-sm font-semibold text-forest-900">
                  {eventLabel(ev.event_type)} · {ev.batch_id}
                </p>
                <p className="text-xs text-charcoal-600">
                  {ev.actor_id} · {ev.location || "—"} · {formatWhen(ev.timestamp)} · block{" "}
                  {ev.block_index ?? "—"}
                </p>
              </li>
            ))}
          </ol>
        )}
      </Panel>
    </div>
  );
}

function Mini({
  label,
  value,
  alert,
}: {
  label: string;
  value: number;
  alert?: boolean;
}) {
  return (
    <div className="organic-panel p-4">
      <p className="text-xs uppercase tracking-[0.16em] text-sage-700">{label}</p>
      <p className={alert ? "font-display text-3xl text-alert" : "font-display text-3xl text-forest-900"}>
        <AnimatedCounter value={value} />
      </p>
    </div>
  );
}
