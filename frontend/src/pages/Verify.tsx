import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { getBatch, type BatchDetail } from "../lib/api";
import { dataString, eventLabel, formatKg, formatWhen, friendlyError } from "../lib/format";
import { EmptyState, LoadingLabel, PageHeader, Panel } from "../components/ui";
import { cn } from "../lib/cn";

export function VerifyPage() {
  const { batchId: routeId } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const initial = routeId || params.get("batch_id") || "";
  const [query, setQuery] = useState(initial);
  const [data, setData] = useState<BatchDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(initial));

  const load = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      setData(await getBatch(id));
    } catch (e) {
      setData(null);
      setError(friendlyError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (routeId) {
      setQuery(routeId);
      void load(routeId);
    }
  }, [routeId, load]);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const id = query.trim();
    if (!id) return;
    navigate(`/verify/${encodeURIComponent(id)}`);
  }

  const harvest = data?.history.find((h) => h.transaction.event_type === "HARVEST");
  const variety = dataString(harvest?.transaction.data, "variety");
  const harvestDate = dataString(harvest?.transaction.data, "harvest_date");
  const compromised = data ? !data.chain_valid : false;
  const verified = Boolean(data?.verified && data.chain_valid);

  return (
    <div>
      <PageHeader
        kicker="Consumer"
        title="Verify product"
        subtitle="A digital product passport sourced only from the live ledger."
        backTo="/"
      />
      <form className="mb-8 flex flex-col gap-3 sm:flex-row" onSubmit={onSubmit}>
        <label className="sr-only" htmlFor="verify-batch">
          Batch ID
        </label>
        <input
          id="verify-batch"
          className="input max-w-xl"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Batch ID"
        />
        <button className="btn-primary" type="submit">
          {loading ? "Verifying" : "Verify"}
        </button>
      </form>
      {loading ? <LoadingLabel>Verifying</LoadingLabel> : null}
      {error ? (
        <EmptyState title="Could not verify" message={error} onRetry={() => void load(query)} />
      ) : null}
      {data ? (
        <div className="overflow-hidden rounded-organ border border-cream-200 bg-cream-50 shadow-panel">
          <div className="relative h-40">
            <img src="/images/consumer-qr.jpg" alt="" className="h-full w-full object-cover" />
            <div className="absolute inset-0 bg-forest-950/55" />
            <p
              className={cn(
                "absolute bottom-4 left-6 font-display text-3xl",
                compromised ? "text-alert-soft" : "text-cream-50",
              )}
            >
              {compromised
                ? "Chain compromised"
                : verified
                  ? "Product verified"
                  : "Record found"}
            </p>
          </div>
          <div className="grid gap-6 p-6 lg:grid-cols-2">
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <Info label="Crop" value={data.batch?.crop} />
              <Info label="Variety" value={variety} />
              <Info label="Farmer" value={data.batch?.farmer} />
              <Info label="Origin" value={data.batch?.location} />
              <Info label="Quantity" value={formatKg(data.batch?.quantity_kg)} />
              <Info label="Grade" value={data.batch?.quality_grade} />
              <Info label="Harvest" value={harvestDate} />
              <Info label="Batch" value={data.batch_id} />
            </dl>
            <div>
              <h2 className="mb-3 font-display text-xl text-forest-900">
                Digital product passport
              </h2>
              <ul className="space-y-2 text-sm">
                <Check ok={!compromised} label="Origin recorded on-chain" />
                <Check ok={data.history.length > 0} label="Supply chain journey present" />
                <Check ok={data.chain_valid} label="Blockchain integrity" />
              </ul>
              <ol className="mt-5 space-y-2 border-l border-sage-200 pl-4 text-sm">
                {data.history.map((h, i) => (
                  <li key={`${h.block_index}-${i}`}>
                    <span className="font-semibold text-forest-800">
                      {eventLabel(h.transaction.event_type || "")}
                    </span>
                    <span className="text-charcoal-600">
                      {" "}
                      · {h.transaction.location} · {formatWhen(h.transaction.timestamp)}
                    </span>
                  </li>
                ))}
              </ol>
              <Link
                className="btn-ghost mt-5 inline-flex"
                to={`/trace/${encodeURIComponent(data.batch_id)}`}
              >
                Open traceability
              </Link>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-[0.14em] text-sage-700">{label}</dt>
      <dd className="text-forest-900">{value || "—"}</dd>
    </div>
  );
}

function Check({ ok, label }: { ok: boolean; label: string }) {
  return (
    <li className="flex items-center gap-2">
      <span className={ok ? "text-emerald-700" : "text-alert"}>{ok ? "✓" : "!"}</span>
      {label}
    </li>
  );
}
