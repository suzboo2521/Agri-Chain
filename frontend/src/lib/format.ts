import type { EventType } from "./api";

export const EVENT_LABELS: Record<EventType, string> = {
  HARVEST: "Harvest",
  QUALITY_CHECK: "Quality check",
  TRANSPORT: "Transport",
  WAREHOUSE_ENTRY: "Warehouse entry",
  PROCESSING: "Processing",
  DISTRIBUTION: "Distribution",
  RETAIL: "Retail",
  DOCUMENT: "Document",
};

export const JOURNEY_STAGES: { key: EventType; label: string; image: string }[] = [
  { key: "HARVEST", label: "Farm", image: "/images/harvest.jpg" },
  { key: "QUALITY_CHECK", label: "Quality", image: "/images/quality.jpg" },
  { key: "TRANSPORT", label: "Transport", image: "/images/transport.jpg" },
  { key: "WAREHOUSE_ENTRY", label: "Warehouse", image: "/images/warehouse.jpg" },
  { key: "PROCESSING", label: "Processing", image: "/images/processing.jpg" },
  { key: "DISTRIBUTION", label: "Collection", image: "/images/collection.jpg" },
  { key: "RETAIL", label: "Retail", image: "/images/retail.jpg" },
];

export function eventLabel(type: string): string {
  return EVENT_LABELS[type as EventType] ?? type.replace(/_/g, " ").toLowerCase();
}

export function shortHash(hash: string, size = 10): string {
  if (!hash) return "—";
  if (hash.length <= size * 2) return hash;
  return `${hash.slice(0, size)}…${hash.slice(-6)}`;
}

export function formatWhen(value: string | number | null | undefined): string {
  if (value == null || value === "") return "—";
  if (typeof value === "number") {
    const ms = value > 1e12 ? value : value * 1000;
    const d = new Date(ms);
    return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleString();
  }
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleString();
}

export function formatKg(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return `${n.toLocaleString(undefined, { maximumFractionDigits: 1 })} kg`;
}

export function extractBatchId(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return "";
  try {
    const url = new URL(trimmed);
    const fromQuery =
      url.searchParams.get("batch_id") || url.searchParams.get("batchId");
    if (fromQuery) return fromQuery.trim();
    const path = url.pathname.match(/\/(?:verify|batch|qr)\/([^/]+)/i);
    if (path) return decodeURIComponent(path[1]);
  } catch {
    /* not a URL */
  }
  const q = trimmed.match(/[?&]batch_id=([^&]+)/i);
  if (q) return decodeURIComponent(q[1]).trim();
  return trimmed;
}

export function dataString(
  data: Record<string, unknown> | undefined,
  key: string,
): string | null {
  if (!data) return null;
  const v = data[key];
  if (v == null || v === "") return null;
  return String(v);
}

export function friendlyError(err: unknown): string {
  if (err && typeof err === "object" && "message" in err) {
    const msg = String((err as { message: unknown }).message);
    if (msg && !msg.includes("Traceback") && !msg.includes("  File ")) return msg;
  }
  return "Something went wrong. Please try again.";
}
