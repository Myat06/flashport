import { useEffect, useRef, useState } from "react";
import { useAuth } from "./hooks/useAuth";
import { useDeclarations } from "./hooks/useDeclarations";
import { useAPI } from "./hooks/useAPI";
import { Sidebar } from "./components/Sidebar";
import { StatsBar } from "./components/StatsBar";
import { DeclarationTable } from "./components/DeclarationTable";
import { DetailPanel } from "./components/DetailPanel";
import { DashboardView } from "./components/DashboardView";
import { AnalysisView } from "./components/AnalysisView";
import { CeisaView } from "./components/CeisaView";
import { OperatorsView } from "./components/OperatorsView";
import { WatchlistView } from "./components/WatchlistView";
import { RiskRulesView } from "./components/RiskRulesView";
import { SLAView } from "./components/SLAView";
import { AuditView } from "./components/AuditView";
import { LoginPage } from "./components/LoginPage";
import { Toast } from "./components/Toast";

const PAGE_TITLES = {
  overview: "Overview",
  declarations: "Declarations",
  analysis: "Analysis",
  ceisa: "CEISA Portal",
  sla: "SLA Dashboard",
  operators: "Operators",
  watchlist: "Watchlist",
  "risk-rules": "Risk Rules",
  audit: "Audit Trail",
};

export default function App() {
  const { token, isAuthenticated, login, logout } = useAuth();
  if (!isAuthenticated) return <LoginPage onLogin={login} />;
  return <Dashboard token={token} onLogout={logout} />;
}

function Dashboard({ token, onLogout }) {
  const { declarations, connected, loading, updateField, submitToCeisa, reviewDeclaration, refetch } =
    useDeclarations(token);
  const api = useAPI(token);
  const [view, setView] = useState("overview");
  const [selected, setSelected] = useState(null);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [batchLoading, setBatchLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const ceisaRefreshRef = useRef(null);

  useEffect(() => {
    const onFocus = () => refetch?.();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [refetch]);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleTabChange = (key) => {
    setView(key);
    setSelected(null);
    setSelectedIds(new Set());
    if (key === "ceisa") ceisaRefreshRef.current?.();
  };

  const handleSelect = (declaration) => setSelected(declaration);
  const handleClosePanel = () => setSelected(null);

  const handleSubmit = async (declarationId) => {
    const result = await submitToCeisa(declarationId);
    const laneLabels = { hijau: "Green Lane ✅", kuning: "Yellow Lane ⚠️", merah: "Red Lane 🔴" };
    showToast(
      `${laneLabels[result.jalur] ?? result.jalur} — ${result.response_code}`,
      result.jalur === "hijau" ? "success" : result.jalur === "merah" ? "error" : "warning"
    );
    return result;
  };

  const handleReview = async (declarationId, status, note) => {
    await reviewDeclaration(declarationId, status, note);
    if (selected?.id === declarationId) {
      setSelected((prev) => ({ ...prev, review_status: status, review_note: note, reviewed_by: "manager" }));
    }
    const labels = { approved: "Approved ✓", rejected: "Rejected ✕", pending: "Reset to pending" };
    showToast(labels[status] ?? status, status === "approved" ? "success" : status === "rejected" ? "error" : "info");
  };

  const handleUpdate = (declarationId, fieldName, value) => {
    updateField(declarationId, fieldName, value);
    if (selected?.id === declarationId) {
      setSelected((prev) => ({
        ...prev,
        extracted_fields: { ...prev.extracted_fields, [fieldName]: value },
      }));
    }
  };

  const handleReprocess = async (declarationId) => {
    const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
    const res = await fetch(`${API}/declarations/${declarationId}/reprocess`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    }).then((r) => r.json());
    showToast(`Re-processed — Risk: ${res.risk_score}%, Confidence: ${res.confidence_badge}`, "success");
    refetch();
    if (selected?.id === declarationId) setSelected(null);
  };

  const handleBatchSubmit = async () => {
    if (selectedIds.size === 0) return;
    setBatchLoading(true);
    try {
      const result = await api.post("/ceisa/batch-submit", {
        declaration_ids: [...selectedIds],
        submitted_by: "manager",
      });
      showToast(`Batch submitted: ${result.submitted} declarations`, "success");
      setSelectedIds(new Set());
      refetch();
    } finally {
      setBatchLoading(false);
    }
  };

  const handleExportCSV = () => {
    api.download("/export/declarations.csv", "flashport_declarations.csv");
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white flex">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      <Sidebar view={view} setView={handleTabChange} connected={connected} onLogout={onLogout} />

      <div className="flex-1 ml-56 min-h-screen flex flex-col">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-gray-950/95 backdrop-blur border-b border-gray-800 px-6 py-3.5 flex items-center justify-between">
          <div>
            <h1 className="text-base font-semibold text-white">{PAGE_TITLES[view]}</h1>
            {(view === "overview" || view === "declarations") && (
              <p className="text-xs text-gray-500 mt-0.5">
                {declarations.length} declaration{declarations.length !== 1 ? "s" : ""} total
              </p>
            )}
          </div>

          {/* Declarations toolbar */}
          {view === "declarations" && (
            <div className="flex items-center gap-2">
              {selectedIds.size > 0 && (
                <button
                  onClick={handleBatchSubmit}
                  disabled={batchLoading}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-xs font-semibold transition-colors"
                >
                  {batchLoading ? "Submitting…" : `Submit ${selectedIds.size} to CEISA`}
                </button>
              )}
              <button
                onClick={handleExportCSV}
                className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                </svg>
                Export CSV
              </button>
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <span className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-red-400"}`} />
                {connected ? "Live" : "Reconnecting…"}
              </div>
            </div>
          )}
        </header>

        {/* Content */}
        <main className="flex-1 px-6 py-6">
          {loading ? (
            <LoadingSkeleton />
          ) : view === "overview" ? (
            <>
              <StatsBar declarations={declarations} />
              <DashboardView
                declarations={declarations}
                onSelect={(d) => { setSelected(d); setView("declarations"); }}
              />
            </>
          ) : view === "declarations" ? (
            <>
              <StatsBar declarations={declarations} />
              <DeclarationTable
                declarations={declarations}
                onSelect={handleSelect}
                selectedIds={selectedIds}
                onSelectIds={setSelectedIds}
              />
            </>
          ) : view === "analysis" ? (
            <AnalysisView declarations={declarations} />
          ) : view === "ceisa" ? (
            <CeisaView token={token} refreshRef={ceisaRefreshRef} />
          ) : view === "sla" ? (
            <SLAView token={token} />
          ) : view === "operators" ? (
            <OperatorsView token={token} />
          ) : view === "watchlist" ? (
            <WatchlistView token={token} />
          ) : view === "risk-rules" ? (
            <RiskRulesView token={token} />
          ) : view === "audit" ? (
            <AuditView token={token} />
          ) : null}
        </main>
      </div>

      {selected && (
        <DetailPanel
          declaration={selected}
          token={token}
          onClose={handleClosePanel}
          onUpdate={handleUpdate}
          onReview={handleReview}
          onSubmit={handleSubmit}
          onReprocess={handleReprocess}
        />
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="grid grid-cols-5 gap-4 mb-6">
        {[1, 2, 3, 4, 5].map((i) => <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl h-24" />)}
      </div>
      {[1, 2, 3, 4].map((i) => <div key={i} className="bg-gray-900 border border-gray-800 rounded-lg h-14" />)}
    </div>
  );
}
