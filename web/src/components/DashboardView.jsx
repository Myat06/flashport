import { useMemo } from "react";

const DOC_LABELS = {
  commercial_invoice: "Commercial Invoice",
  bill_of_lading: "Bill of Lading",
  packing_list: "Packing List",
};

export function DashboardView({ declarations }) {
  const stats = useMemo(() => {
    const byJalur = { green: 0, yellow: 0, red: 0 };
    const byConfidence = { high: 0, medium: 0, low: 0 };
    const byDocType = {};
    let ceisaReady = 0;

    for (const d of declarations) {
      byJalur[d.risk_badge ?? "yellow"]++;
      byConfidence[d.confidence_badge ?? "medium"]++;
      const dt = d.document_type ?? "commercial_invoice";
      byDocType[dt] = (byDocType[dt] ?? 0) + 1;
      if (d.ceisa_ready) ceisaReady++;
    }

    return { byJalur, byConfidence, byDocType, ceisaReady };
  }, [declarations]);

  const total = declarations.length;
  const pct = (n) => (total ? Math.round((n / total) * 100) : 0);
  const recent = declarations.slice(0, 6);

  return (
    <div className="space-y-5">
      {/* Top KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <BigStat label="Total Scans" value={total} colour="text-blue-400" sub="declarations processed" />
        <BigStat label="Jalur Hijau" value={stats.byJalur.green} colour="text-emerald-400" sub={`${pct(stats.byJalur.green)}% of total`} />
        <BigStat label="Jalur Kuning" value={stats.byJalur.yellow} colour="text-yellow-400" sub={`${pct(stats.byJalur.yellow)}% of total`} />
        <BigStat label="Jalur Merah" value={stats.byJalur.red} colour="text-red-400" sub={`${pct(stats.byJalur.red)}% of total`} />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <ChartCard title="Jalur Distribution">
          <BarRow label="Jalur Hijau" value={stats.byJalur.green} pct={pct(stats.byJalur.green)} barColour="bg-emerald-500" textColour="text-emerald-400" />
          <BarRow label="Jalur Kuning" value={stats.byJalur.yellow} pct={pct(stats.byJalur.yellow)} barColour="bg-yellow-500" textColour="text-yellow-400" />
          <BarRow label="Jalur Merah" value={stats.byJalur.red} pct={pct(stats.byJalur.red)} barColour="bg-red-500" textColour="text-red-400" />
        </ChartCard>

        <ChartCard title="OCR Confidence Level">
          <BarRow label="High" value={stats.byConfidence.high} pct={pct(stats.byConfidence.high)} barColour="bg-blue-500" textColour="text-blue-400" />
          <BarRow label="Medium" value={stats.byConfidence.medium} pct={pct(stats.byConfidence.medium)} barColour="bg-orange-500" textColour="text-orange-400" />
          <BarRow label="Low" value={stats.byConfidence.low} pct={pct(stats.byConfidence.low)} barColour="bg-red-500" textColour="text-red-400" />
        </ChartCard>

        <ChartCard title="Document Types">
          {Object.keys(stats.byDocType).length === 0 ? (
            <p className="text-xs text-gray-600">No data yet.</p>
          ) : (
            Object.entries(stats.byDocType)
              .sort(([, a], [, b]) => b - a)
              .map(([type, count]) => (
                <BarRow
                  key={type}
                  label={DOC_LABELS[type] ?? type}
                  value={count}
                  pct={pct(count)}
                  barColour="bg-blue-500"
                  textColour="text-blue-400"
                />
              ))
          )}
        </ChartCard>

        <ChartCard title="CEISA Readiness">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <div className="text-2xl font-bold text-emerald-400">{stats.ceisaReady}</div>
                <div className="text-xs text-gray-400 mt-0.5">Ready to submit</div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-yellow-400">{total - stats.ceisaReady}</div>
                <div className="text-xs text-gray-400 mt-0.5">Needs review</div>
              </div>
            </div>
            {total > 0 && (
              <div>
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Progress</span>
                  <span>{pct(stats.ceisaReady)}% ready</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
                  <div
                    className="h-3 bg-emerald-500 rounded-full transition-all"
                    style={{ width: `${pct(stats.ceisaReady)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </ChartCard>
      </div>

      {/* Recent activity */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Recent Activity</h3>
        {recent.length === 0 ? (
          <p className="text-sm text-gray-600">No scans yet — waiting for field operators.</p>
        ) : (
          <div className="divide-y divide-gray-800">
            {recent.map((d) => {
              const id = d.declaration_id ?? d.id;
              const badge = d.risk_badge ?? "yellow";
              const badgeLabel = { green: "Hijau", yellow: "Kuning", red: "Merah" }[badge];
              const badgeColour = { green: "text-emerald-400 bg-emerald-900/40 border-emerald-800", yellow: "text-yellow-400 bg-yellow-900/40 border-yellow-800", red: "text-red-400 bg-red-900/40 border-red-800" }[badge];
              return (
                <div key={id} className="flex items-center justify-between py-2.5">
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate">{DOC_LABELS[d.document_type] ?? d.document_type ?? "Document"}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {d.scanned_at ? new Date(d.scanned_at).toLocaleString("id-ID") : "—"}
                      {" · "}
                      {d.operator_id ?? "Field Operator"}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-3 shrink-0">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${badgeColour}`}>{badgeLabel}</span>
                    <span className="text-xs text-gray-500 w-12 text-right">{d.risk_score ?? 0}% risk</span>
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

function BigStat({ label, value, colour, sub }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-4">
      <div className={`text-3xl font-bold ${colour}`}>{value}</div>
      <div className="text-sm font-medium text-gray-200 mt-0.5">{label}</div>
      <div className="text-xs text-gray-500 mt-0.5">{sub}</div>
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{title}</h3>
      {children}
    </div>
  );
}

function BarRow({ label, value, pct, barColour, textColour }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-gray-300">{label}</span>
        <span className={textColour}>{value} ({pct}%)</span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-2">
        <div className={`h-2 rounded-full transition-all ${barColour}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
