import { useEffect } from "react";
import { useCeisaSubmissions } from "../hooks/useCeisaSubmissions";

const DOC_LABELS = {
  commercial_invoice: "Commercial Invoice",
  bill_of_lading: "Bill of Lading",
  packing_list: "Packing List",
};

const JALUR_CONFIG = {
  hijau: {
    label: "JALUR HIJAU",
    code: "SP2-200",
    desc: "Disetujui — Pengeluaran Segera",
    bar: "bg-emerald-500",
    badge: "bg-emerald-900/40 border-emerald-700 text-emerald-300",
    icon: "✓",
    iconBg: "bg-emerald-500",
    border: "border-l-emerald-500",
    glow: "shadow-emerald-900/30",
  },
  kuning: {
    label: "JALUR KUNING",
    code: "SP2-412",
    desc: "Ditahan — Verifikasi Dokumen",
    bar: "bg-yellow-500",
    badge: "bg-yellow-900/40 border-yellow-700 text-yellow-300",
    icon: "!",
    iconBg: "bg-yellow-500",
    border: "border-l-yellow-500",
    glow: "shadow-yellow-900/30",
  },
  merah: {
    label: "JALUR MERAH",
    code: "SP2-500",
    desc: "Ditahan — Pemeriksaan Fisik",
    bar: "bg-red-500",
    badge: "bg-red-900/40 border-red-700 text-red-300",
    icon: "✕",
    iconBg: "bg-red-500",
    border: "border-l-red-500",
    glow: "shadow-red-900/30",
  },
};

export function CeisaView({ token, refreshRef }) {
  const { submissions, loading, refresh } = useCeisaSubmissions(token);

  // Allow parent to trigger refresh when tab becomes active
  useEffect(() => {
    if (refreshRef) refreshRef.current = refresh;
  }, [refresh, refreshRef]);

  const counts = submissions.reduce(
    (acc, s) => { acc[s.jalur] = (acc[s.jalur] || 0) + 1; return acc; },
    { hijau: 0, kuning: 0, merah: 0 }
  );

  return (
    <div className="space-y-5">
      {/* Portal header */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold tracking-widest text-gray-500 uppercase">Direktorat Jenderal Bea dan Cukai</span>
            </div>
            <h1 className="text-lg font-bold text-white">Portal CEISA — Customs Clearance System</h1>
            <p className="text-xs text-gray-500 mt-0.5">Sistem Informasi Ekspor Impor · Mode Simulasi Phase 1</p>
          </div>
          <button
            onClick={refresh}
            className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
          >
            ↻ Refresh
          </button>
        </div>

        {/* Summary bar */}
        <div className="grid grid-cols-3 gap-3 mt-4">
          {[
            { key: "hijau", label: "Jalur Hijau", colour: "text-emerald-400" },
            { key: "kuning", label: "Jalur Kuning", colour: "text-yellow-400" },
            { key: "merah", label: "Jalur Merah", colour: "text-red-400" },
          ].map(({ key, label, colour }) => (
            <div key={key} className="bg-gray-800/60 rounded-lg px-4 py-3 text-center">
              <div className={`text-2xl font-bold ${colour}`}>{counts[key]}</div>
              <div className="text-xs text-gray-400 mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Submissions list */}
      <div className="space-y-3">
        {loading ? (
          <LoadingSkeleton />
        ) : submissions.length === 0 ? (
          <div className="text-center py-20 text-gray-600">
            <div className="text-4xl mb-3">🏛️</div>
            <div className="text-sm">Belum ada pengajuan PIB — submit deklarasi dari Live Feed untuk melihat respon CEISA.</div>
          </div>
        ) : (
          submissions.map((s) => <SubmissionRow key={s.id} submission={s} />)
        )}
      </div>
    </div>
  );
}

function SubmissionRow({ submission }) {
  const cfg = JALUR_CONFIG[submission.jalur] ?? JALUR_CONFIG.kuning;
  const submittedAt = submission.submitted_at
    ? new Date(submission.submitted_at).toLocaleString("id-ID")
    : "—";

  return (
    <div className={`bg-gray-900 border border-gray-800 border-l-4 ${cfg.border} rounded-xl p-4 shadow-lg ${cfg.glow}`}>
      <div className="flex items-start gap-4">
        {/* Jalur icon */}
        <div className={`w-10 h-10 rounded-full ${cfg.iconBg} flex items-center justify-center text-white font-bold text-sm shrink-0`}>
          {cfg.icon}
        </div>

        <div className="flex-1 min-w-0">
          {/* Top row */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${cfg.badge}`}>
              {cfg.label}
            </span>
            <span className="text-xs font-mono text-gray-400">{submission.response_code}</span>
            {submission.ceisa_reference && (
              <span className="text-xs font-mono text-blue-400 bg-blue-900/30 border border-blue-800 px-2 py-0.5 rounded-full">
                {submission.ceisa_reference}
              </span>
            )}
          </div>

          {/* Response message */}
          <p className="text-sm text-gray-200 mt-2 leading-relaxed">{submission.response_message}</p>

          {/* Meta row */}
          <div className="flex items-center gap-4 mt-3 text-xs text-gray-500 flex-wrap">
            <span>📄 {DOC_LABELS[submission.document_type] ?? submission.document_type ?? "—"}</span>
            {submission.risk_score != null && (
              <span>⚠ Risiko {submission.risk_score}%</span>
            )}
            <span>👤 {submission.submitted_by ?? "Manager"}</span>
            <span>🕐 {submittedAt}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl h-24" />
      ))}
    </div>
  );
}
