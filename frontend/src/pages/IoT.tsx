import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { toast } from "sonner";
import {
  addSensor,
  getAnomalies,
  getBatch,
  streamSensors,
  type AnomaliesResponse,
  type SensorReading,
} from "../lib/api";
import { friendlyError } from "../lib/format";
import { EmptyState, Field, LoadingLabel, PageHeader, Panel } from "../components/ui";

export function IoTPage() {
  const [params] = useSearchParams();
  const [batchId, setBatchId] = useState(params.get("batch_id") || "");
  const [readings, setReadings] = useState<SensorReading[]>([]);
  const [anomalies, setAnomalies] = useState<AnomaliesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (id: string) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const [batch, anom] = await Promise.all([getBatch(id.trim()), getAnomalies(id.trim())]);
      setReadings(batch.sensor_readings || []);
      setAnomalies(anom);
    } catch (e) {
      setError(friendlyError(e));
      setReadings([]);
      setAnomalies(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const q = params.get("batch_id");
    if (q) {
      setBatchId(q);
      void load(q);
    }
  }, [params, load]);

  const chart = useMemo(
    () =>
      readings.map((r, i) => ({
        i,
        temperature: r.temperature,
        humidity: r.humidity,
        anomaly: r.anomaly_flag ? r.temperature : null,
      })),
    [readings],
  );

  async function onStream(inject: boolean) {
    if (!batchId.trim()) {
      toast.error("Enter a batch ID first.");
      return;
    }
    setBusy(true);
    try {
      const res = await streamSensors(batchId.trim(), 10, inject);
      toast.success(res.message);
      await load(batchId.trim());
    } catch (e) {
      toast.error(friendlyError(e));
    } finally {
      setBusy(false);
    }
  }

  async function onManual(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    setBusy(true);
    try {
      const res = await addSensor({
        batch_id: batchId.trim(),
        temperature: Number(fd.get("temperature")),
        humidity: Number(fd.get("humidity")),
        gps_lat: Number(fd.get("gps_lat") || 16.58),
        gps_lon: Number(fd.get("gps_lon") || 82),
      });
      toast.message(res.anomaly ? "Reading stored — anomaly flagged." : res.message);
      await load(batchId.trim());
    } catch (err) {
      toast.error(friendlyError(err));
    } finally {
      setBusy(false);
    }
  }

  const last = readings[readings.length - 1];

  return (
    <div>
      <PageHeader
        kicker="Cold chain"
        title="IoT monitoring"
        subtitle="Temperature, humidity and GPS from the live sensor store. Anomalies come from the Isolation Forest path on the API."
        backTo="/"
      />
      <form
        className="mb-6 flex flex-col gap-3 sm:flex-row"
        onSubmit={(e) => {
          e.preventDefault();
          void load(batchId);
        }}
      >
        <label className="sr-only" htmlFor="iot-batch">
          Batch ID
        </label>
        <input
          id="iot-batch"
          className="input max-w-xl"
          value={batchId}
          onChange={(e) => setBatchId(e.target.value)}
          placeholder="Batch ID"
        />
        <button className="btn-primary" type="submit">
          {loading ? "Loading sensors" : "Load sensors"}
        </button>
      </form>
      <div className="mb-6 flex flex-wrap gap-2">
        <button className="btn-primary" type="button" disabled={busy} onClick={() => void onStream(false)}>
          {busy ? "Streaming" : "Start stream"}
        </button>
        <button className="btn-ghost" type="button" disabled={busy} onClick={() => void onStream(true)}>
          Stream with anomaly
        </button>
      </div>
      {error ? (
        <EmptyState title="Sensors unavailable" message={error} onRetry={() => void load(batchId)} />
      ) : null}
      {loading ? <LoadingLabel>Loading sensors</LoadingLabel> : null}
      {last ? (
        <div className="mb-6 grid gap-3 sm:grid-cols-3">
          <Metric label="Temperature" value={`${last.temperature} °C`} alert={Boolean(last.anomaly_flag)} />
          <Metric label="Humidity" value={`${last.humidity} %`} />
          <Metric label="GPS" value={`${last.gps_lat.toFixed(4)}, ${last.gps_lon.toFixed(4)}`} />
        </div>
      ) : null}
      {chart.length ? (
        <Panel className="mb-6 h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chart}>
              <CartesianGrid stroke="#efe8d4" />
              <XAxis dataKey="i" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="temperature" stroke="#1f6b48" dot={false} />
              <Line type="monotone" dataKey="humidity" stroke="#a88840" dot={false} />
              <Line type="monotone" dataKey="anomaly" stroke="#b42318" dot />
            </LineChart>
          </ResponsiveContainer>
        </Panel>
      ) : null}
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <h2 className="mb-4 font-display text-xl text-forest-900">Manual reading</h2>
          <form className="grid gap-3 sm:grid-cols-2" onSubmit={onManual}>
            <Field label="Temperature">
              <input className="input" name="temperature" type="number" step="0.1" required />
            </Field>
            <Field label="Humidity">
              <input className="input" name="humidity" type="number" step="0.1" required />
            </Field>
            <Field label="GPS lat">
              <input className="input" name="gps_lat" type="number" step="0.0001" defaultValue="16.58" />
            </Field>
            <Field label="GPS lon">
              <input className="input" name="gps_lon" type="number" step="0.0001" defaultValue="82" />
            </Field>
            <button className="btn-primary sm:col-span-2 w-fit" disabled={busy}>
              {busy ? "Recording" : "Post sensor"}
            </button>
          </form>
        </Panel>
        <Panel>
          <h2 className="mb-4 font-display text-xl text-forest-900">Anomalies</h2>
          {!anomalies?.anomalies.length ? (
            <p className="text-sm text-charcoal-600">
              {anomalies ? `No anomalies in ${anomalies.total} readings.` : "Load a batch to inspect flags."}
            </p>
          ) : (
            <ul className="space-y-2 text-sm">
              {anomalies.anomalies.map((a, i) => (
                <li key={a.id ?? i} className="rounded-2xl bg-alert-soft px-3 py-2 text-alert">
                  {a.temperature} °C · {a.humidity}% · {a.timestamp}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  alert,
}: {
  label: string;
  value: string;
  alert?: boolean;
}) {
  return (
    <div className="organic-panel p-4">
      <p className="text-xs uppercase tracking-[0.16em] text-sage-700">{label}</p>
      <p className={alert ? "mt-1 font-display text-2xl text-alert" : "mt-1 font-display text-2xl text-forest-900"}>
        {value}
      </p>
    </div>
  );
}
