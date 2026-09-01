import { type FormEvent, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import {
  getDocuments,
  uploadDocument,
  verifyDocument,
  type DocumentRecord,
  type DocumentVerifyResponse,
} from "../lib/api";
import { friendlyError, shortHash } from "../lib/format";
import { EmptyState, Field, LoadingLabel, PageHeader, Panel } from "../components/ui";
import { cn } from "../lib/cn";

export function DocumentsPage() {
  const [params] = useSearchParams();
  const [batchId, setBatchId] = useState(params.get("batch_id") || "");
  const [docs, setDocs] = useState<DocumentRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [verdict, setVerdict] = useState<DocumentVerifyResponse | null>(null);

  const load = useCallback(async (id: string) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getDocuments(id.trim());
      setDocs(res.documents);
    } catch (e) {
      setError(friendlyError(e));
      setDocs([]);
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

  async function onUpload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const file = fd.get("file");
    if (!(file instanceof File) || !file.size) {
      toast.error("Choose a file to hash.");
      return;
    }
    setBusy(true);
    try {
      const res = await uploadDocument(batchId.trim(), file, String(fd.get("doc_type") || "certificate"));
      toast.success("SHA-256 recorded on-chain.");
      void res;
      e.currentTarget.reset();
      await load(batchId.trim());
    } catch (err) {
      toast.error(friendlyError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onVerify(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const file = fd.get("file");
    if (!(file instanceof File) || !file.size) {
      toast.error("Choose a file to verify.");
      return;
    }
    setBusy(true);
    try {
      setVerdict(await verifyDocument(batchId.trim(), file));
    } catch (err) {
      toast.error(friendlyError(err));
    } finally {
      setBusy(false);
    }
  }

  const modified = verdict?.status === "MODIFIED";
  const authentic = verdict?.status === "MATCH";

  return (
    <div>
      <PageHeader
        kicker="Off-chain files"
        title="Documents"
        subtitle="Certificates stay on disk. Only the SHA-256 the API computed is anchored on the chain."
        backTo="/"
      />
      <form
        className="mb-6 flex flex-col gap-3 sm:flex-row"
        onSubmit={(e) => {
          e.preventDefault();
          void load(batchId);
        }}
      >
        <label className="sr-only" htmlFor="doc-batch">
          Batch ID
        </label>
        <input
          id="doc-batch"
          className="input max-w-xl"
          value={batchId}
          onChange={(e) => setBatchId(e.target.value)}
          placeholder="Batch ID"
        />
        <button className="btn-primary" type="submit">
          {loading ? "Loading documents" : "Load documents"}
        </button>
      </form>
      {error ? (
        <EmptyState title="Documents unavailable" message={error} onRetry={() => void load(batchId)} />
      ) : null}
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <h2 className="mb-4 font-display text-xl text-forest-900">Upload</h2>
          <form className="grid gap-3" onSubmit={onUpload}>
            <Field label="Document type">
              <input className="input" name="doc_type" defaultValue="certificate" />
            </Field>
            <Field label="File">
              <input className="input" name="file" type="file" required />
            </Field>
            <button className="btn-primary w-fit" disabled={busy}>
              {busy ? "Anchoring hash" : "Upload & anchor"}
            </button>
          </form>
        </Panel>
        <Panel>
          <h2 className="mb-4 font-display text-xl text-forest-900">Verify file</h2>
          <form className="grid gap-3" onSubmit={onVerify}>
            <Field label="File to check">
              <input className="input" name="file" type="file" required />
            </Field>
            <button className="btn-primary w-fit" disabled={busy}>
              {busy ? "Checking hash" : "Verify document"}
            </button>
          </form>
          {verdict ? (
            <div
              className={cn(
                "mt-4 rounded-2xl p-4",
                modified ? "bg-alert-soft text-alert" : authentic ? "bg-emerald-100 text-emerald-800" : "bg-sage-50",
              )}
            >
              <p className="font-display text-2xl">
                {authentic ? "Authentic" : modified ? "Modified" : verdict.status}
              </p>
              <p className="mt-1 text-sm">{verdict.message}</p>
              <p className="hash mt-3">expected {shortHash(verdict.expected, 14)}</p>
              <p className="hash">actual {shortHash(verdict.actual, 14)}</p>
            </div>
          ) : null}
        </Panel>
      </div>
      <Panel className="mt-6">
        <h2 className="mb-4 font-display text-xl text-forest-900">On record</h2>
        {loading ? <LoadingLabel>Loading documents</LoadingLabel> : null}
        {!loading && docs.length === 0 ? (
          <p className="text-sm text-charcoal-600">No documents for this batch.</p>
        ) : (
          <ul className="space-y-3">
            {docs.map((d) => (
              <li key={d.id} className="rounded-2xl bg-sage-50 p-3 text-sm">
                <p className="font-semibold text-forest-900">{d.filename}</p>
                <p className="hash mt-1">{d.sha256}</p>
                <p className="mt-1 text-xs text-charcoal-600">{d.uploaded_at}</p>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
