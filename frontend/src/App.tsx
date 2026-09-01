import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { AnalyticsPage } from "./pages/Analytics";
import { BatchDetailPage } from "./pages/BatchDetail";
import { BatchesPage } from "./pages/Batches";
import { BlockchainPage } from "./pages/Blockchain";
import { DashboardPage } from "./pages/Dashboard";
import { DocumentsPage } from "./pages/Documents";
import { IoTPage } from "./pages/IoT";
import { QRPage } from "./pages/QR";
import { RegisterPage } from "./pages/Register";
import { RiskPage } from "./pages/Risk";
import { TraceStagePage, TraceabilityPage } from "./pages/Traceability";
import { VerifyPage } from "./pages/Verify";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="batches" element={<BatchesPage />} />
        <Route path="batches/:batchId" element={<BatchDetailPage />} />
        <Route path="trace" element={<TraceabilityPage />} />
        <Route path="trace/:batchId" element={<TraceabilityPage />} />
        <Route path="trace/:batchId/:stageIndex" element={<TraceStagePage />} />
        <Route path="qr" element={<QRPage />} />
        <Route path="verify" element={<VerifyPage />} />
        <Route path="verify/:batchId" element={<VerifyPage />} />
        <Route path="blockchain" element={<BlockchainPage />} />
        <Route path="iot" element={<IoTPage />} />
        <Route path="risk" element={<RiskPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
