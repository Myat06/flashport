import { useMemo } from "react";

const DOC_LABELS = {
  commercial_invoice: "Commercial Invoice",
  bill_of_lading: "Bill of Lading",
  packing_list: "Packing List",
};

export function DashboardView({ declarations, onSelect }) {
  const stats = useMemo(() => {
    const byLane = { green: 0, yellow: 0, red: 0 };
    const byConfidence = { high: 0, medium: 0, low: 0 };
    const byDocType = {};
    const byReview = { pending: 0, approved: 0, rejected: 0 };
    let ceisaReady = 0;
    let totalRisk = 0;

    for (const d of declarations) {
      byLane[d.risk_badge ?? "yellow"]++;
      byConfidence[d.confidence_badge ?? "medium"]++;
      const dt = d.document_type ?? "commercial_invoice";
      byDocType[dt] = (byDocType[dt] ?? 0) + 1;
      const rs = d.review_status ?? "pending";
      byReview[rs] = (byReview[rs] ?? 0) + 1;
      if (d.ceisa_ready) ceisaReady++;
      totalRisk += d.risk_score ?? 0;
    }

    const n = declarations.length || 1;
    return { byLane, byConfidence, byDocType, byReview, ceisaReady, avgRisk: Math.round(totalRisk / n) };
  }, [declarations]);

  const total = declarations.length;
  const pct = (n) => (total ? Math.round((n / total) * 100) : 0);
  const recent = declarations.slice(0, 8);

  return (
    <div className="space-y-6">
      {/* Review status KPIs */}
      <div className="grid grid-cols-3 gap-4">
        <KPICard
          label="Pending Review"
          value={stats.byReview.pending}
          sub={`${pct(stats.byReview.pending)}% of total`}
          colour="text-yellow-400"
          dot="bg-yellow-400"
          bg="bg-yellow-900/10 border-yellow-800/30"
        />
        <KPICard
          label="Approved"
          value={stats.byReview.approved}
          sub={`${pct(stats.byReview.approved)}% of total`}
          colour="text-emerald-400"
          dot="bg-emerald-400"
          bg="bg-emerald-900/10 border-emerald-800/30"
        />
        <KPICard
          label="Rejected"
          value={stats.byReview.rejected}
          sub={`${pct(stats.byReview.rejected)}% of total`}
          colour="text-red-400"
          dot="bg-red-400"
          bg="bg-red-900/10 border-red-800/30"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Lane distribution */}
        <SectionCard title="CEISA Lane Distribution">
          {total === 0 ? <Empty /> : (
            <div className="space-y-3">
              {[
                { label: "Green Lane", value: stats.byLane.green, bar: "bg-emerald-500", text: "text-emerald-400" },
                { label: "Yellow Lane", value: stats.byLane.yellow, bar: "bg-yellow-500", text: "text-yellow-400" },
                { label: "Red Lane", value: stats.byLane.red, bar: "bg-red-500", text: "text-red-400" },
              ].map(({ label, value, bar, text }) => (
                <div key={label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">{label}</span>
                    <span className={text}>{value} · {pct(value)}%</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div className={`h-2 rounded-full ${bar} transition-all`} style={{ width: `${pct(value)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>

        {/* OCR Confidence */}
        <SectionCard title="OCR Confidence">
          {total === 0 ? <Empty /> : (
            <div className="space-y-3">
              {[
                { label: "High", value: stats.byConfidence.high, bar: "bg-blue-500", text: "text-blue-400" },
                { label: "Medium", value: stats.byConfidence.medium, bar: "bg-orange-500", text: "text-orange-400" },
                { label: "Low", value: stats.byConfidence.low, bar: "bg-red-500", text: "text-red-400" },
              ].map(({ label, value, bar, text }) => (
                <div key={label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">{label}</span>
                    <span className={text}>{value} · {pct(value)}%</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div className={`h-2 rounded-full ${bar} transition-all`} style={{ width: `${pct(value)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>

        {/* Document types */}
        <SectionCard title="Document Types">
          {Object.keys(stats.byDocType).length === 0 ? <Empty /> : (
            <div className="space-y-3">
              {Object.entries(stats.byDocType).sort(([, a], [, b]) => b - a).map(([type, count]) => (
                <div key={type}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">{DOC_LABELS[type] ?? type}</span>
                    <span className="text-blue-400">{count} · {pct(count)}%</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div className="h-2 rounded-full bg-blue-500 transition-all" style={{ width: `${pct(count)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>

        {/* CEISA readiness */}
        <SectionCard title="CEISA Readiness">
          <div className="space-y-4">
            <div className="flex justify-between">
              <div>
                <div className="text-3xl font-bold text-emerald-400">{stats.ceisaReady}</div>
                <div className="text-xs text-gray-500 mt-0.5">Ready to submit</div>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-gray-500">{total - stats.ceisaReady}</div>
                <div className="text-xs text-gray-500 mt-0.5">Needs review</div>
              </div>
            </div>
            {total > 0 && (
              <div>
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span>Progress</span>
                  <span>{pct(stats.ceisaReady)}% ready</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
                  <div className="h-3 bg-emerald-500 rounded-full transition-all" style={{ width: `${pct(stats.ceisaReady)}%` }} />
                </div>
              </div>
            )}
            <div className="text-xs text-gray-600">Avg risk score: {stats.avgRisk}%</div>
          </div>
        </SectionCard>
      </div>

      {/* Recent activity */}
      <SectionCard title="Recent Activity">
        {recent.length === 0 ? (
          <p className="text-sm text-gray-600">No scans yet — waiting for field operators.</p>
        ) : (
          <div className="divide-y divide-gray-800">
            {recent.map((d) => {
              const reviewStatus = d.review_status ?? "pending";
              const reviewCfg = {
                pending: "text-yellow-400",
                approved: "text-emerald-400",
                rejected: "text-red-400",
              }[reviewStatus];
              const reviewLabel = { pending: "Pending", approved: "Approved", rejected: "Rejected" }[reviewStatus];
              const riskCfg = {
                green: "text-emerald-400",
                yellow: "text-yellow-400",
                red: "text-red-400",
              }[d.risk_badge ?? "yellow"];

              return (
                <div
                  key={d.id}
                  onClick={() => onSelect(d)}
                  className="flex items-center justify-between py-3 cursor-pointer hover:bg-gray-800/40 -mx-4 px-4 rounded-lg transition-colors"
                >
                  <div className="min-w-0">
                    <div className="text-sm font-medium">{DOC_LABELS[d.document_type] ?? "Document"}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {d.scanned_at ? new Date(d.scanned_at).toLocaleString() : "—"}
                      {d.operator_id ? ` · ${d.operator_id}` : ""}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 ml-4 shrink-0">
                    <span className={`text-xs font-semibold ${riskCfg}`}>{d.risk_score ?? 0}% risk</span>
                    <span className={`text-xs font-semibold ${reviewCfg}`}>{reviewLabel}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

function KPICard({ label, value, sub, colour, dot, bg }) {
  return (
    <div className={`border rounded-xl px-5 py-5 ${bg}`}>
      <div className="flex items-center gap-2 mb-3">
        <span className={`w-2 h-2 rounded-full ${dot}`} />
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{label}</span>
      </div>
      <div className={`text-4xl font-bold ${colour}`}>{value}</div>
      <div className="text-xs text-gray-600 mt-1">{sub}</div>
    </div>
  );
}

function SectionCard({ title, children }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-4">{title}</h3>
      {children}
    </div>
  );
}

function Empty() {
  return <p className="text-xs text-gray-600">No data yet — waiting for scans.</p>;
}
