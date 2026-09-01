import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { registerProduct, type RegistrationResponse } from "../lib/api";
import { friendlyError } from "../lib/format";
import { Field, HashLine, Modal, PageHeader, Panel } from "../components/ui";

export function RegisterPage() {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<RegistrationResponse | null>(null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const crop = String(fd.get("crop") || "").trim();
    const farmer = String(fd.get("farmer") || "").trim();
    const location = String(fd.get("location") || "").trim();
    const quantity_kg = Number(fd.get("quantity_kg"));
    const quality_grade = String(fd.get("quality_grade") || "A").trim() || "A";
    const variety = String(fd.get("variety") || "").trim();
    const harvest_date = String(fd.get("harvest_date") || "").trim();
    if (!crop || !farmer || !location || !(quantity_kg > 0)) {
      toast.error("Crop, farmer, location and quantity are required.");
      return;
    }
    setBusy(true);
    try {
      const res = await registerProduct({
        crop,
        farmer,
        location,
        quantity_kg,
        quality_grade,
        variety: variety || null,
        harvest_date: harvest_date || null,
      });
      setResult(res);
      toast.success("Batch registered on-chain.");
    } catch (err) {
      toast.error(friendlyError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        kicker="On-chain origin"
        title="Register a batch"
        subtitle="Creates a unique batch ID and records a HARVEST event on the AgriChain ledger."
        backTo="/"
        backLabel="BACK TO DASHBOARD"
      />
      <Panel className="max-w-2xl">
        <form className="grid gap-4" onSubmit={onSubmit}>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Crop">
              <input className="input" name="crop" required placeholder="Rice" />
            </Field>
            <Field label="Variety">
              <input className="input" name="variety" placeholder="BPT-5204" />
            </Field>
            <Field label="Farmer">
              <input className="input" name="farmer" required placeholder="Farmer_001" />
            </Field>
            <Field label="Origin / location">
              <input className="input" name="location" required placeholder="Konaseema" />
            </Field>
            <Field label="Quantity (kg)">
              <input
                className="input"
                name="quantity_kg"
                type="number"
                min={0.1}
                step="0.1"
                required
                placeholder="2500"
              />
            </Field>
            <Field label="Quality grade">
              <input className="input" name="quality_grade" defaultValue="A" />
            </Field>
            <Field label="Harvest date">
              <input className="input" name="harvest_date" type="date" />
            </Field>
          </div>
          <button className="btn-primary mt-2 w-fit" type="submit" disabled={busy}>
            {busy ? "Registering" : "Register batch"}
          </button>
        </form>
      </Panel>

      <Modal
        open={Boolean(result)}
        title="Batch registered"
        onClose={() => setResult(null)}
        footer={
          result ? (
            <>
              <Link className="btn-primary" to={`/batches/${encodeURIComponent(result.batch_id)}`}>
                View batch
              </Link>
              <Link className="btn-ghost" to={`/trace/${encodeURIComponent(result.batch_id)}`}>
                Traceability
              </Link>
              <Link className="btn-ghost" to={`/qr?batch_id=${encodeURIComponent(result.batch_id)}`}>
                Generate QR
              </Link>
              <Link className="btn-ghost" to="/">
                Back to dashboard
              </Link>
            </>
          ) : null
        }
      >
        {result ? (
          <div className="space-y-3">
            <p>{result.message}</p>
            <p className="font-mono text-lg text-forest-900">{result.batch_id}</p>
            <p className="text-sm">Block index {result.block_index}</p>
            <HashLine value={result.block_hash} label="Block hash" />
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
