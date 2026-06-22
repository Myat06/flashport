import { useEffect, useState } from "react";
import { useAPI } from "../hooks/useAPI";

export function SLAView({ token }) {
  const api = useAPI(token);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = () => api.get("/sla").then((d) => { setData(d); setLoading(false); });
  useEffect(() => { load(); }, []); // eslint-disable-line

  if (loading) return <div className="text-center py-20 text-gray-600">Loading SLA metrics…</div>;
  if (!data) return null;

  const throughputEntries = Object.entries(data.daily_throughput).sort(([a], [b]) => b.localeCompare(a)).slice(0, 7);
  const maxThroughput = Math.max(...throughputEntries.map(([, v]) => v), 1);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">SLA Dashboard</h2>
          <p className="text-xs text-gray-500 mt-0.5">Target: review within {data.sla_target_hours}h of scan</p>
        </div>
        <button onClick={load} className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors">
          ↻ Refresh
        </button>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-4 gap-4">
        <SLACard label="Avg Review Time" value={data.avg_review_hours != null ? `${data.avg_review_hours}h` : "—"} colour="text-blue-400" />
        <SLACard label="Pending Review" value={data.pending_review} colour="text-yellow-400" />
        <SLACard label="Reviewed" value={data.reviewed} colour="text-emerald-400" />
        <SLACard label="Overdue" value={data.overdue_count} colour={data.overdue_count > 0 ? "text-red-400" : "text-emerald-400"} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Daily throughput */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-4">Daily Throughput (last 7 days)</h3>
          {throughputEntries.length === 0 ? (
            <p className="text-xs text-gray-600">No reviews yet.</p>
          ) : (
            <div className="space-y-2">
              {throughputEntries.map(([day, count]) => (
                <div key={day}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">{day}</span>
                    <span className="text-blue-400">{count} reviewed</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div className="h-2 rounded-full bg-blue-500 transition-all" style={{ width: `${Math.round((count / maxThroughput) * 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Overdue list */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Overdue Declarations
            {data.overdue_count > 0 && (
              <span className="ml-2 px-1.5 py-0.5 bg-red-900/40 text-red-400 border border-red-800 rounded-full text-xs">
                {data.overdue_count}
              </span>
            )}
          </h3>
          {data.overdue.length === 0 ? (
            <div className="flex flex-col items-center py-6 text-center">
              <div className="text-3xl mb-2">✅</div>
              <p className="text-xs text-gray-500">All declarations reviewed within SLA</p>
            </div>
          ) : (
            <div className="space-y-2">
              {data.overdue.map((d) => (
                <div key={d.id} className="bg-red-900/10 border border-red-900/40 rounded-lg px-3 py-2.5">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="text-xs font-medium text-white">{d.document_type?.replace(/_/g, " ") ?? "Document"}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{d.operator_id ?? "Unknown operator"}</div>
                    </div>
                    <span className="text-xs font-bold text-red-400">{d.hours_pending}h overdue</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SLACard({ label, value, colour }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-4">
      <div className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-2">{label}</div>
      <div className={`text-3xl font-bold ${colour}`}>{value}</div>
    </div>
  );
}
