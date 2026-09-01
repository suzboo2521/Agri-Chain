import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getBatch, type BatchDetail, type HistoryItem } from "../lib/api";
import { eventLabel, formatWhen, friendlyError, shortHash } from "../lib/format";
import { EmptyState, LoadingLabel, PageHeader, Panel } from "../components/ui";
import { TraceTimeline } from "../components/TraceTimeline";

export function TraceabilityPage() {
  const { batchId } = useParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState(batchId || "");
  const [data, setData] = useState<BatchDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (id: string) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setData(await getBatch(id.trim()));
    } catch (e) {
      setData(null);
      setError(friendlyError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (batchId) {
      setQuery(batchId);
      void load(batchId);
    }
  }, [batchId, load]);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    const id = query.trim();
    if (!id) return;
    navigate(`/trace/${encodeURIComponent(id)}`);
  }

  return (
    <div>
      <PageHeader
        kicker="Provenance"
        title="Traceability"
        subtitle="Search a batch and walk each stage from harvest to retail."
        backTo="/"
      />
      <form className="mb-8 flex flex-col gap-3 sm:flex-row" onSubmit={onSearch}>
        <label className="sr-only" htmlFor="trace-batch">
          Batch ID
        </label>
        <input
          id="trace-batch"
          className="input max-w-xl"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="RICE-KONASE-2026-0001"
        />
        <button className="btn-primary" type="submit">
          {loading ? "Tracing" : "Trace batch"}
        </button>
      </form>
      {loading ? <LoadingLabel>Tracing journey</LoadingLabel> : null}
      {error ? (
        <EmptyState title="No journey found" message={error} onRetry={() => void load(query)} />
      ) : null}
      {data ? (
        <Panel>
          <p className="mb-6 font-mono text-sm text-forest-800">{data.batch_id}</p>
          <TraceTimeline batchId={data.batch_id} history={data.history} />
        </Panel>
      ) : null}
    </div>
  );
}

export function TraceStagePage() {
  const { batchId = "", stageIndex = "0" } = useParams();
  const [item, setItem] = useState<HistoryItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const detail = await getBatch(batchId);
      const idx = Number(stageIndex);
      const row = detail.history[idx];
      if (!row) throw new Error("That stage is not on this batch journey.");
      setItem(row);
    } catch (e) {
      setError(friendlyError(e));
      setItem(null);
    } finally {
      setLoading(false);
    }
  }, [batchId, stageIndex]);

  useEffect(() => {
    void load();
  }, [load]);

  const tx = item?.transaction;

  return (
    <div>
      <PageHeader
        kicker={tx ? eventLabel(tx.event_type || "") : "Stage"}
        title={tx?.actor_id || "Journey stage"}
        backTo={`/trace/${encodeURIComponent(batchId)}`}
        backLabel="BACK TO TRACEABILITY"
      />
      {loading ? <LoadingLabel>Loading stage</LoadingLabel> : null}
      {error ? (
        <EmptyState title="Stage unavailable" message={error} onRetry={() => void load()} />
      ) : null}
      {item && tx ? (
        <Panel className="max-w-2xl">
          <dl className="grid gap-4 sm:grid-cols-2">
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
              <dt className="text-xs uppercase tracking-[0.14em] text-sage-700">Block index</dt>
              <dd>{item.block_index}</dd>
            </div>
          </dl>
          <p className="mt-4 text-xs uppercase tracking-[0.14em] text-sage-700">Hash</p>
          <p className="hash mt-1 text-forest-800">{item.block_hash}</p>
          {tx.data_hash ? (
            <p className="hash mt-2 text-charcoal-600">data {shortHash(tx.data_hash, 14)}</p>
          ) : null}
          <Link className="btn-ghost mt-6 inline-flex" to={`/trace/${encodeURIComponent(batchId)}`}>
            Back to traceability
          </Link>
        </Panel>
      ) : null}
    </div>
  );
}
