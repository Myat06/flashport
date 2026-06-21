import { useEffect, useRef, useState } from "react";
import { useAuth } from "./hooks/useAuth";
import { useDeclarations } from "./hooks/useDeclarations";
import { DeclarationCard } from "./components/DeclarationCard";
import { DashboardView } from "./components/DashboardView";
import { AnalysisView } from "./components/AnalysisView";
import { CeisaView } from "./components/CeisaView";
import { LoginPage } from "./components/LoginPage";
import { Toast } from "./components/Toast";

const VIEWS = [
  { key: "feed", label: "Live Feed" },
  { key: "dashboard", label: "Dashboard" },
  { key: "analysis", label: "Analysis" },
  { key: "ceisa", label: "Portal CEISA" },
];

export default function App() {
  const { token, isAuthenticated, login, logout } = useAuth();

  if (!isAuthenticated) return <LoginPage onLogin={login} />;

  return <Dashboard token={token} onLogout={logout} />;
}

function Dashboard({ token, onLogout }) {
  const { declarations, connected, loading, updateField, submitToCeisa, refetch } = useDeclarations(token);
  const [view, setView] = useState("feed");
  const [filter, setFilter] = useState("all");
  const [toast, setToast] = useState(null);
  const ceisaRefreshRef = useRef(null);

  // Refetch declarations when window regains focus
  useEffect(() => {
    const onFocus = () => refetch?.();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [refetch]);

  const handleTabChange = (key) => {
    setView(key);
    if (key === "ceisa") ceisaRefreshRef.current?.();
  };

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleSubmit = async (declarationId) => {
    const result = await submitToCeisa(declarationId);
    const jalurLabels = { hijau: "Jalur Hijau ✅", kuning: "Jalur Kuning ⚠️", merah: "Jalur Merah 🔴" };
    showToast(
      `${jalurLabels[result.jalur] ?? result.jalur} — ${result.response_code}`,
      result.jalur === "hijau" ? "success" : result.jalur === "merah" ? "error" : "warning"
    );
    return result;
  };

  const counts = declarations.reduce(
    (acc, d) => { acc[d.risk_badge ?? "yellow"] = (acc[d.risk_badge ?? "yellow"] || 0) + 1; return acc; },
    { green: 0, yellow: 0, red: 0 }
  );

  const filtered = filter === "all"
    ? declarations
    : declarations.filter((d) => d.risk_badge === filter);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      {/* Top bar */}
      <header className="sticky top-0 z-10 border-b border-gray-800 bg-gray-950/95 backdrop-blur px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-blue-400 font-bold text-xl tracking-tight">⚡ FlashPort</span>
          <span className="text-gray-600 text-sm hidden sm:inline">Customs Admin Dashboard</span>
        </div>
        <div className="flex items-center gap-4">
          {view === "feed" && (
            <div className="hidden sm:flex gap-3 text-xs font-medium">
              <span className="text-emerald-400">{counts.green} Hijau</span>
              <span className="text-yellow-400">{counts.yellow} Kuning</span>
              <span className="text-red-400">{counts.red} Merah</span>
            </div>
          )}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs">
              <span className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-red-400"}`} />
              <span className="text-gray-400">{connected ? "Live" : "Reconnecting…"}</span>
            </div>
            <button
              onClick={onLogout}
              className="text-xs px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white rounded-lg transition-colors"
            >
              Keluar
            </button>
          </div>
        </div>
      </header>

      {/* View navigation */}
      <div className="border-b border-gray-800 bg-gray-950 px-6">
        <nav className="flex gap-1 max-w-5xl mx-auto">
          {VIEWS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => handleTabChange(key)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                view === key
                  ? "border-blue-500 text-blue-400"
                  : "border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-700"
              }`}
            >
              {label}
              {key === "feed" && declarations.length > 0 && (
                <span className="ml-1.5 px-1.5 py-0.5 bg-blue-900/60 text-blue-300 text-xs rounded-full">
                  {declarations.length}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6">
        {loading ? (
          <LoadingSkeleton />
        ) : view === "dashboard" ? (
          <DashboardView declarations={declarations} />
        ) : view === "analysis" ? (
          <AnalysisView declarations={declarations} />
        ) : view === "ceisa" ? (
          <CeisaView token={token} refreshRef={ceisaRefreshRef} />
        ) : (
          <FeedView
            declarations={declarations}
            filtered={filtered}
            counts={counts}
            filter={filter}
            setFilter={setFilter}
            onUpdate={updateField}
            onSubmit={handleSubmit}
          />
        )}
      </main>
    </div>
  );
}

function FeedView({ declarations, filtered, counts, filter, setFilter, onUpdate, onSubmit }) {
  return (
    <>
      {/* Filter tabs */}
      <div className="flex gap-2 mb-4">
        {[
          { key: "all", label: `All (${declarations.length})` },
          { key: "green", label: `Hijau (${counts.green})` },
          { key: "yellow", label: `Kuning (${counts.yellow})` },
          { key: "red", label: `Merah (${counts.red})` },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filter === key
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Cards */}
      {filtered.length === 0 ? (
        <div className="text-center py-20 text-gray-600">
          <div className="text-5xl mb-4">📄</div>
          <div className="text-sm">
            {declarations.length === 0
              ? "Waiting for field scans — declarations appear here in real time."
              : "No declarations match this filter."}
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((d) => (
            <DeclarationCard
              key={d.declaration_id ?? d.id}
              declaration={d}
              onUpdate={onUpdate}
              onSubmit={onSubmit}
            />
          ))}
        </div>
      )}
    </>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-gray-900 border border-gray-800 rounded-lg h-16" />
      ))}
    </div>
  );
}
