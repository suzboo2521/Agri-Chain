import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import {
  EVENT_TYPES,
  addEvent,
  getBatch,
  type BatchDetail,
  type EventType,
} from "../lib/api";
import { dataString, eventLabel, formatKg, friendlyError } from "../lib/format";
import { EmptyState, Field, LoadingLabel, PageHeader, Panel } from "../components/ui";

export function BatchDetailPage() {
  const { batchId = "" } = useParams();
  const [data, setData] = useState<BatchDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await getBatch(batchId));
    } catch (e) {
      setError(friendlyError(e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [batchId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onEvent(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    setBusy(true);
    try {
      const note = String(fd.get("note") || "").trim();
      await addEvent({
        batch_id: batchId,
        event_type: String(fd.get("event_type")) as EventType,
        actor_id: String(fd.get("actor_id") || "").trim(),
        location: String(fd.get("location") || "").trim(),
        data: note ? { note } : {},
      });
      toast.success("Event mined onto the chain.");
      e.currentTarget.reset();
      await load();
    } catch (err) {
      toast.error(friendlyError(err));
    } finally {
      setBusy(false);
    }
  }

  const harvest = data?.history.find((h) => h.transaction.event_type === "HARVEST");
  const variety = dataString(harvest?.transaction.data, "variety");
  const harvestDate = dataString(harvest?.transaction.data, "harvest_date");

  return (
    <div>
      <PageHeader
        kicker="Batch passport"
        title={batchId}
        subtitle="Actions for this harvest across trace, verify, QR, documents, sensors and risk."
        backTo="/batches"
        backLabel="BACK"
      />
      {loading ? <LoadingLabel>Loading batch</LoadingLabel> : null}
      {error ? (
        <EmptyState title="Batch not available" message={error} onRetry={() => void load()} />
      ) : null}
      {data ? (
        <>
          <div className="mb-6 flex flex-wrap gap-2">
            <Link className="btn-primary" to={`/trace/${encodeURIComponent(batchId)}`}>
              Trace
            </Link>
            <Link className="btn-ghost" to={`/verify/${encodeURIComponent(batchId)}`}>
              Verify
            </Link>
            <Link className="btn-ghost" to={`/qr?batch_id=${encodeURIComponent(batchId)}`}>
              QR
            </Link>
            <Link className="btn-ghost" to={`/documents?batch_id=${encodeURIComponent(batchId)}`}>
              Docs
            </Link>
            <Link className="btn-ghost" to={`/iot?batch_id=${encodeURIComponent(batchId)}`}>
              IoT
            </Link>
            <Link className="btn-ghost" to={`/risk?batch_id=${encodeURIComponent(batchId)}`}>
              AI risk
            </Link>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <Panel>
              <h2 className="mb-4 font-display text-xl text-forest-900">Origin</h2>
              <dl className="grid grid-cols-2 gap-3 text-sm">
                <Info label="Crop" value={data.batch?.crop} />
                <Info label="Variety" value={variety} />
                <Info label="Farmer" value={data.batch?.farmer} />
                <Info label="Origin" value={data.batch?.location} />
                <Info label="Quantity" value={formatKg(data.batch?.quantity_kg)} />
                <Info label="Grade" value={data.batch?.quality_grade} />
                <Info label="Harvest" value={harvestDate} />
                <Info label="Status" value={data.batch?.status} />
                <Info label="Events" value={String(data.history.length)} />
                <Info
                  label="Chain"
                  value={data.chain_valid ? "Intact" : "Compromised"}
                  alert={!data.chain_valid}
                />
              </dl>
            </Panel>
            <Panel>
              <h2 className="mb-4 font-display text-xl text-forest-900">Add journey event</h2>
              <form className="grid gap-3" onSubmit={onEvent}>
                <Field label="Event type">
                  <select className="input" name="event_type" defaultValue="QUALITY_CHECK">
                    {EVENT_TYPES.filter((t) => t !== "HARVEST" && t !== "DOCUMENT").map((t) => (
                      <option key={t} value={t}>
                        {eventLabel(t)}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Actor">
                  <input className="input" name="actor_id" required placeholder="Inspector_01" />
                </Field>
                <Field label="Location">
                  <input className="input" name="location" required placeholder="Amalapuram" />
                </Field>
                <Field label="Note (optional)">
                  <input className="input" name="note" />
                </Field>
                <button className="btn-primary w-fit" disabled={busy}>
                  {busy ? "Recording" : "Record event"}
                </button>
              </form>
            </Panel>
          </div>
        </>
      ) : null}
    </div>
  );
}

function Info({
  label,
  value,
  alert,
}: {
  label: string;
  value?: string | null;
  alert?: boolean;
}) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-[0.14em] text-sage-700">{label}</dt>
      <dd className={alert ? "text-alert" : "text-forest-900"}>{value || "—"}</dd>
    </div>
  );
}
