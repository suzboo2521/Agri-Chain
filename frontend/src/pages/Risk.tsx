import { type FormEvent, useState } from "react";
import { toast } from "sonner";
import { calculateRisk, type RiskResult } from "../lib/api";
import { friendlyError } from "../lib/format";
import { Field, PageHeader, Panel } from "../components/ui";
import { RiskGauge } from "../components/RiskGauge";
import { cn } from "../lib/cn";

export function RiskPage() {
  const [result, setResult] = useState<RiskResult | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    setBusy(true);
    try {
      const res = await calculateRisk({
        temperature: Number(fd.get("temperature")),
        humidity: Number(fd.get("humidity")),
        delay_hours: Number(fd.get("delay_hours")),
        quality_score: Number(fd.get("quality_score")),
        quantity_kg: Number(fd.get("quantity_kg") || 2000),
        transport_distance_km: Number(fd.get("transport_distance_km") || 80),
      });
      setResult(res);
    } catch (err) {
      toast.error(friendlyError(err));
    } finally {
      setBusy(false);
    }
  }

  const high = result?.level.toUpperCase() === "HIGH";
  const atRisk = result?.ml_prediction === "AT_RISK";

  return (
    <div>
      <PageHeader
        kicker="Explainable AI"
        title="AI risk"
        subtitle="Rule-based 0–100 score plus an optional Random Forest label from the trained model on the API."
        backTo="/"
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <form className="grid gap-3 sm:grid-cols-2" onSubmit={onSubmit}>
            <Field label="Temperature">
              <input className="input" name="temperature" type="number" step="0.1" required defaultValue="28" />
            </Field>
            <Field label="Humidity">
              <input className="input" name="humidity" type="number" step="0.1" required defaultValue="70" />
            </Field>
            <Field label="Delay (hours)">
              <input className="input" name="delay_hours" type="number" step="0.1" required defaultValue="4" />
            </Field>
            <Field label="Quality score">
              <input className="input" name="quality_score" type="number" step="0.1" required defaultValue="82" />
            </Field>
            <Field label="Quantity (kg)">
              <input className="input" name="quantity_kg" type="number" step="0.1" defaultValue="2000" />
            </Field>
            <Field label="Distance (km)">
              <input className="input" name="transport_distance_km" type="number" step="0.1" defaultValue="80" />
            </Field>
            <button className="btn-primary sm:col-span-2 w-fit" disabled={busy}>
              {busy ? "Calculating risk" : "Calculate risk"}
            </button>
          </form>
        </Panel>
        <Panel>
          {result ? (
            <div>
              <RiskGauge score={result.score} level={result.level} />
              {result.ml_prediction ? (
                <p
                  className={cn(
                    "mt-4 text-center text-xs font-semibold uppercase tracking-[0.2em]",
                    atRisk && high ? "text-alert" : "text-forest-700",
                  )}
                >
                  ML {result.ml_prediction}
                </p>
              ) : (
                <p className="mt-4 text-center text-xs text-charcoal-600">
                  No ML model loaded on the API — showing the rule score only.
                </p>
              )}
              <ul className="mt-6 space-y-2 text-sm">
                {Object.entries(result.factors).map(([k, v]) => (
                  <li key={k} className="flex justify-between border-b border-cream-200 py-1">
                    <span className="capitalize">{k.replace(/_/g, " ")}</span>
                    <span className={v > 0 && high ? "text-alert" : "text-forest-800"}>{v}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-sm text-charcoal-600">
              Enter conditions and calculate. Red is reserved for high risk.
            </p>
          )}
        </Panel>
      </div>
    </div>
  );
}
