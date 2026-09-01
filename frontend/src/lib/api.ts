/**
 * Single HTTP client for the original AgriChain FastAPI app
 * (`uvicorn backend.main:app` from the repo root).
 * Components must not call fetch() directly.
 */
const API_BASE = (
  import.meta.env.VITE_AGRICHAIN_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

export { API_BASE };

export class ApiError extends Error {
  status: number;
  constructor(message: string, status = 0) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export type EventType =
  | "HARVEST"
  | "QUALITY_CHECK"
  | "TRANSPORT"
  | "WAREHOUSE_ENTRY"
  | "PROCESSING"
  | "DISTRIBUTION"
  | "RETAIL"
  | "DOCUMENT";

export const EVENT_TYPES: EventType[] = [
  "HARVEST",
  "QUALITY_CHECK",
  "TRANSPORT",
  "WAREHOUSE_ENTRY",
  "PROCESSING",
  "DISTRIBUTION",
  "RETAIL",
  "DOCUMENT",
];

export type HealthResponse = {
  message: string;
  status: string;
  blocks: number;
  chain_valid: boolean;
};

export type ProductRegistration = {
  crop: string;
  farmer: string;
  location: string;
  quantity_kg: number;
  quality_grade?: string;
  variety?: string | null;
  harvest_date?: string | null;
};

export type RegistrationResponse = {
  message: string;
  batch_id: string;
  block_index: number;
  block_hash: string;
};

export type SupplyChainEvent = {
  batch_id: string;
  event_type: EventType;
  actor_id: string;
  location: string;
  timestamp?: string | null;
  data?: Record<string, unknown>;
};

export type EventResponse = {
  message: string;
  block_index: number;
  block_hash: string;
};

export type ChainTransaction = {
  batch_id?: string;
  event_type?: string;
  actor_id?: string;
  location?: string;
  timestamp?: string;
  data?: Record<string, unknown>;
  data_hash?: string;
};

export type ChainBlock = {
  index: number;
  timestamp: number;
  transactions: ChainTransaction[];
  previous_hash: string;
  nonce: number;
  hash: string;
};

export type VerifyResponse = {
  valid: boolean;
  message: string;
  blocks: number;
};

export type BatchRecord = {
  batch_id: string;
  crop: string;
  farmer: string;
  location: string;
  quantity_kg: number;
  quality_grade: string | null;
  status: string;
  created_at: string;
  events?: number;
  has_alert?: boolean;
};

export type HistoryItem = {
  block_index: number;
  block_hash: string;
  timestamp: number;
  transaction: ChainTransaction;
};

export type SensorReading = {
  id?: number;
  batch_id: string;
  temperature: number;
  humidity: number;
  gps_lat: number;
  gps_lon: number;
  timestamp: string;
  anomaly_flag?: number;
};

export type BatchDetail = {
  batch_id: string;
  batch: BatchRecord | null;
  history: HistoryItem[];
  sensor_readings: SensorReading[];
  chain_valid: boolean;
  verified: boolean;
};

export type SensorInput = {
  batch_id: string;
  temperature: number;
  humidity: number;
  gps_lat?: number;
  gps_lon?: number;
  timestamp?: string | null;
};

export type SensorAddResponse = {
  message: string;
  anomaly: boolean;
};

export type SensorStreamResponse = {
  message: string;
  anomalies: number;
};

export type AnomaliesResponse = {
  batch_id: string;
  total: number;
  anomalies: SensorReading[];
};

export type RiskInput = {
  temperature: number;
  humidity: number;
  delay_hours: number;
  quality_score: number;
  quantity_kg?: number;
  transport_distance_km?: number;
};

export type RiskResult = {
  score: number;
  level: string;
  factors: Record<string, number>;
  ml_prediction: string | null;
};

export type DocumentUploadResponse = {
  message: string;
  batch_id: string;
  filename: string;
  doc_type: string;
  sha256: string;
  block_index: number;
  block_hash: string;
};

export type DocumentRecord = {
  id: number;
  batch_id: string;
  filename: string;
  filepath: string | null;
  sha256: string;
  uploaded_at: string;
};

export type DocumentListResponse = {
  batch_id: string;
  documents: DocumentRecord[];
};

export type DocumentVerifyResponse = {
  batch_id: string;
  filename: string;
  status: "MATCH" | "MODIFIED" | string;
  message: string;
  expected: string;
  actual: string;
  block_index: number;
};

export type BatchesResponse = {
  batches: BatchRecord[];
};

export type EventRow = {
  id: number;
  batch_id: string;
  event_type: string;
  actor_id: string;
  location: string | null;
  timestamp: string;
  data_hash: string | null;
  block_index: number | null;
  data: Record<string, unknown>;
};

export type ActivityResponse = {
  events: EventRow[];
};

export type AnalyticsResponse = {
  total_batches: number;
  total_kg: number;
  total_blocks: number;
  chain_valid: boolean;
  crop_mix: Record<string, number>;
  status_mix: Record<string, number>;
  farmer_mix: Record<string, number>;
  event_mix: Record<string, number>;
  recent_events: EventRow[];
  recent_sensors: SensorReading[];
  temperature_alerts: number;
  quality_failures: number;
  documents: DocumentRecord[];
};

export type StatsResponse = {
  total_batches: number;
  verified: number;
  flagged: number;
  high_risk: number;
  quality_failures: number;
  temperature_alerts: number;
  total_blocks: number;
  chain_valid: boolean;
};

export type TamperResponse = {
  message: string;
  batch_id: string;
  block_index: number;
  field: string;
  old_value: unknown;
  new_value: unknown;
  chain_valid: boolean;
};

export type ResetResponse = {
  message: string;
  blocks: number;
};

function friendlyHttpError(status: number, detail: unknown): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return "";
      })
      .filter(Boolean);
    if (parts.length) return parts.join(" · ");
  }
  if (status === 404) return "We could not find that record.";
  if (status === 400) return "The request could not be completed.";
  if (status >= 500) return "The AgriChain API had a problem. Please try again.";
  return "Something went wrong. Please try again.";
}

async function parseError(res: Response): Promise<string> {
  try {
    const body: unknown = await res.json();
    if (body && typeof body === "object" && "detail" in body) {
      return friendlyHttpError(res.status, (body as { detail: unknown }).detail);
    }
  } catch {
    /* ignore non-JSON */
  }
  return friendlyHttpError(res.status, null);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new ApiError(
      "The AgriChain API is offline. Start the backend and try again.",
      0,
    );
  }
  if (!res.ok) {
    throw new ApiError(await parseError(res), res.status);
  }
  if (res.status === 204) return undefined as T;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return (await res.json()) as T;
  }
  return (await res.json()) as T;
}

function jsonHeaders(): HeadersInit {
  return { "Content-Type": "application/json", Accept: "application/json" };
}

export async function health(): Promise<HealthResponse> {
  return request<HealthResponse>("/");
}

export async function registerProduct(
  body: ProductRegistration,
): Promise<RegistrationResponse> {
  return request<RegistrationResponse>("/register", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(body),
  });
}

export async function addEvent(body: SupplyChainEvent): Promise<EventResponse> {
  return request<EventResponse>("/event", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(body),
  });
}

export async function getBatch(batchId: string): Promise<BatchDetail> {
  return request<BatchDetail>(`/batch/${encodeURIComponent(batchId)}`);
}

export async function getBlockchain(): Promise<ChainBlock[]> {
  return request<ChainBlock[]>("/blockchain");
}

export async function verifyBlockchain(): Promise<VerifyResponse> {
  return request<VerifyResponse>("/verify");
}

export async function addSensor(body: SensorInput): Promise<SensorAddResponse> {
  return request<SensorAddResponse>("/sensor", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(body),
  });
}

export async function streamSensors(
  batchId: string,
  n = 10,
  injectAnomaly = false,
): Promise<SensorStreamResponse> {
  const q = new URLSearchParams({
    batch_id: batchId,
    n: String(n),
    inject_anomaly: String(injectAnomaly),
  });
  return request<SensorStreamResponse>(`/sensor/stream?${q.toString()}`, {
    method: "POST",
  });
}

export async function getAnomalies(batchId: string): Promise<AnomaliesResponse> {
  return request<AnomaliesResponse>(`/anomalies/${encodeURIComponent(batchId)}`);
}

export async function calculateRisk(body: RiskInput): Promise<RiskResult> {
  return request<RiskResult>("/risk", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(body),
  });
}

export async function getQR(batchId: string): Promise<string> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/qr/${encodeURIComponent(batchId)}`);
  } catch {
    throw new ApiError(
      "The AgriChain API is offline. Start the backend and try again.",
      0,
    );
  }
  if (!res.ok) {
    throw new ApiError(await parseError(res), res.status);
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export async function uploadDocument(
  batchId: string,
  file: File,
  docType = "certificate",
): Promise<DocumentUploadResponse> {
  const form = new FormData();
  form.append("batch_id", batchId);
  form.append("doc_type", docType);
  form.append("file", file);
  return request<DocumentUploadResponse>("/document", {
    method: "POST",
    body: form,
  });
}

export async function getDocuments(batchId: string): Promise<DocumentListResponse> {
  return request<DocumentListResponse>(`/document/${encodeURIComponent(batchId)}`);
}

export async function verifyDocument(
  batchId: string,
  file: File,
): Promise<DocumentVerifyResponse> {
  const form = new FormData();
  form.append("batch_id", batchId);
  form.append("file", file);
  return request<DocumentVerifyResponse>("/document/verify", {
    method: "POST",
    body: form,
  });
}

export async function getBatches(): Promise<BatchesResponse> {
  return request<BatchesResponse>("/batches");
}

export async function getActivity(limit = 25): Promise<ActivityResponse> {
  return request<ActivityResponse>(`/activity?limit=${limit}`);
}

export async function getAnalytics(): Promise<AnalyticsResponse> {
  return request<AnalyticsResponse>("/analytics");
}

export async function getStats(): Promise<StatsResponse> {
  return request<StatsResponse>("/stats");
}

export async function tamperDemo(): Promise<TamperResponse> {
  return request<TamperResponse>("/debug/tamper", { method: "POST" });
}

export async function resetLedger(): Promise<ResetResponse> {
  return request<ResetResponse>("/debug/reset", { method: "POST" });
}
