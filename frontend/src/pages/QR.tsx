import { type FormEvent, useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Html5Qrcode } from "html5-qrcode";
import { toast } from "sonner";
import { getQR } from "../lib/api";
import { extractBatchId, friendlyError } from "../lib/format";
import { EmptyState, PageHeader, Panel } from "../components/ui";

export function QRPage() {
  const [params] = useSearchParams();
  const [batchId, setBatchId] = useState(params.get("batch_id") || "");
  const [qrUrl, setQrUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [scanning, setScanning] = useState(false);
  const scannerRef = useRef<Html5Qrcode | null>(null);

  useEffect(() => {
    const fromQuery = params.get("batch_id");
    if (fromQuery) setBatchId(fromQuery);
  }, [params]);

  useEffect(() => {
    return () => {
      if (qrUrl) URL.revokeObjectURL(qrUrl);
      void stopScan();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function stopScan() {
    const s = scannerRef.current;
    scannerRef.current = null;
    setScanning(false);
    if (!s) return;
    try {
      if (s.isScanning) await s.stop();
    } catch {
      /* already stopped */
    }
    try {
      s.clear();
    } catch {
      /* ignore */
    }
  }

  async function loadQr(id: string) {
    setBusy(true);
    setError(null);
    if (qrUrl) URL.revokeObjectURL(qrUrl);
    setQrUrl(null);
    try {
      setQrUrl(await getQR(id));
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setBusy(false);
    }
  }

  async function onVerify(e: FormEvent) {
    e.preventDefault();
    const id = extractBatchId(batchId);
    if (!id) {
      toast.error("Enter a batch ID or scan a code first.");
      return;
    }
    setBatchId(id);
    await loadQr(id);
  }

  async function startScan() {
    setError(null);
    try {
      const scanner = new Html5Qrcode("qr-reader");
      scannerRef.current = scanner;
      setScanning(true);
      await scanner.start(
        { facingMode: "environment" },
        { fps: 8, qrbox: { width: 220, height: 220 } },
        (decoded) => {
          const id = extractBatchId(decoded);
          setBatchId(id);
          toast.success("QR captured.");
          void stopScan();
          void loadQr(id);
        },
        () => undefined,
      );
    } catch {
      setScanning(false);
      setError("Camera is not available. Upload an image or enter a batch ID.");
    }
  }

  async function onUpload(file: File | null) {
    if (!file) return;
    try {
      const scanner = new Html5Qrcode("qr-file");
      const decoded = await scanner.scanFile(file, true);
      scanner.clear();
      const id = extractBatchId(decoded);
      setBatchId(id);
      toast.success("QR image read.");
      await loadQr(id);
    } catch {
      toast.error("Could not read a QR code in that image.");
    }
  }

  return (
    <div>
      <PageHeader
        kicker="Scan & generate"
        title="QR verification"
        subtitle="Scan a pack, upload a code, or generate the real QR image from the ledger."
        backTo="/"
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <div className="scan-frame relative overflow-hidden rounded-organ bg-forest-950">
            <span className="scan-corners-bl" />
            <span className="scan-corners-br" />
            <div id="qr-reader" className="min-h-[240px] w-full" />
            {scanning ? (
              <div className="pointer-events-none absolute inset-x-8 top-8 z-10 h-0.5 animate-scan-line bg-gold-400/80" />
            ) : (
              <p className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center px-6 text-center text-sm text-cream-100/80">
                Point the camera at a product QR
              </p>
            )}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {scanning ? (
              <button className="btn-ghost" type="button" onClick={() => void stopScan()}>
                Stop scan
              </button>
            ) : (
              <button className="btn-primary" type="button" onClick={() => void startScan()}>
                Scan
              </button>
            )}
            <label className="btn-ghost cursor-pointer">
              Upload image
              <input
                type="file"
                accept="image/*"
                className="sr-only"
                onChange={(e) => void onUpload(e.target.files?.[0] || null)}
              />
            </label>
          </div>
          <div id="qr-file" className="hidden" />
        </Panel>
        <Panel>
          <form className="grid gap-3" onSubmit={onVerify}>
            <label className="text-xs font-semibold uppercase tracking-[0.16em] text-sage-700">
              Enter batch ID
              <input
                className="input mt-1.5"
                value={batchId}
                onChange={(e) => setBatchId(e.target.value)}
                placeholder="RICE-KONASE-2026-0001"
              />
            </label>
            <button className="btn-primary w-fit" disabled={busy}>
              {busy ? "Generating" : "Verify"}
            </button>
          </form>
          {error ? (
            <div className="mt-4">
              <EmptyState title="QR unavailable" message={error} onRetry={() => void loadQr(batchId)} />
            </div>
          ) : null}
          {qrUrl ? (
            <div className="mt-6">
              <img src={qrUrl} alt={`QR for ${batchId}`} className="max-w-[240px] rounded-2xl border border-cream-200" />
              <div className="mt-4 flex flex-wrap gap-2">
                <Link className="btn-primary" to={`/verify/${encodeURIComponent(extractBatchId(batchId))}`}>
                  Open passport
                </Link>
                <Link className="btn-ghost" to={`/trace/${encodeURIComponent(extractBatchId(batchId))}`}>
                  Traceability
                </Link>
              </div>
            </div>
          ) : null}
        </Panel>
      </div>
    </div>
  );
}
