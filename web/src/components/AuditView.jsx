import { useEffect, useState } from "react";
import { useAPI } from "../hooks/useAPI";

const ACTION_COLOURS = {
  "declaration.created": "text-blue-400 bg-blue-900/20 border-blue-800",
  "declaration.approved": "text-emerald-400 bg-emerald-900/20 border-emerald-800",
  "declaration.rejected": "text-red-400 bg-red-900/20 border-red-800",
  "declaration.pending": "text-yellow-400 bg-yellow-900/20 border-yellow-800",
  "declaration.reprocessed": "text-purple-400 bg-purple-900/20 border-purple-800",
  "ceisa.submitted": "text-cyan-400 bg-cyan-900/20 border-cyan-800",
};

const ACTION_ICONS = {
  "declaration.created": "📄",
  "declaration.approved": "✓",
  "declaration.rejected": "✕",
  "declaration.pending": "●",
  "declaration.reprocessed": "↻",
  "ceisa.submitted": "🏛️",
};

export function AuditView({ token }) {
  const api = useAPI(token);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => api.get("/audit?limit=100").then((data) => { setLogs(data); setLoading(false); });
  useEffect(() => { load(); }, []); // eslint-disable-line

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Audit Trail</h2>
          <p className="text-xs text-gray-500 mt-0.5">All actions logged — last 100 events</p>
        </div>
        <button onClick={load} className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors">
          ↻ Refresh
        </button>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        {loading ? (
          <div className="text-center py-16 text-gray-600 text-sm">Loading…</div>
        ) : logs.length === 0 ? (
          <div className="text-center py-16 text-gray-600">
            <div className="text-4xl mb-3">📋</div>
            <div className="text-sm">No audit events yet — actions will appear here.</div>
          </div>
        ) : (
          <div className="divide-y divide-gray-800/60">
            {logs.map((log) => {
              const colourCls = ACTION_COLOURS[log.action] ?? "text-gray-400 bg-gray-800 border-gray-700";
              const icon = ACTION_ICONS[log.action] ?? "●";
              return (
                <div key={log.id} className="flex items-start gap-4 px-5 py-3.5">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border shrink-0 mt-0.5 ${colourCls}`}>
                    {icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${colourCls}`}>
                        {log.action}
                      </span>
                      <span className="text-xs text-gray-500">by {log.performed_by}</span>
                    </div>
                    {log.entity_id && (
                      <div className="text-xs text-gray-600 font-mono mt-1">{log.entity_type} · {log.entity_id}</div>
                    )}
                    {log.detail && Object.keys(log.detail).length > 0 && (
                      <div className="text-xs text-gray-500 mt-1">
                        {Object.entries(log.detail).map(([k, v]) => `${k}: ${v}`).join(" · ")}
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-gray-600 shrink-0">
                    {log.created_at ? new Date(log.created_at).toLocaleString() : "—"}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
