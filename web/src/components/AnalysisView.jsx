import { useMemo } from "react";

const DOC_LABELS = {
  commercial_invoice: "Commercial Invoice",
  bill_of_lading: "Bill of Lading",
  packing_list: "Packing List",
};

const FIELD_LABELS = {
  hs_code: "HS Code",
  invoice_value: "Invoice Value",
  container_id: "Container ID",
  importer: "Importer",
  exporter: "Exporter",
  net_weight: "Net Weight",
  gross_weight: "Gross Weight",
  vessel_name: "Vessel Name",
  port_of_origin: "Port of Origin",
  invoice_number: "Invoice No.",
  carton_count: "Carton Count",
};

export function AnalysisView({ declarations }) {
  const data = useMemo(() => {
    const riskBuckets = [
      { label: "0–29 (Hijau)", min: 0, max: 29, colour: "bg-emerald-500", textColour: "text-emerald-400", count: 0 },
      { label: "30–69 (Kuning)", min: 30, max: 69, colour: "bg-yellow-500", textColour: "text-yellow-400", count: 0 },
      { label: "70–100 (Merah)", min: 70, max: 100, colour: "bg-red-500", textColour: "text-red-400", count: 0 },
    ];
    const flaggedFreq = {};
    const riskByDoc = {};
    const countByDoc = {};
    let totalExtracted = 0;
    let totalMissing = 0;
    let totalRisk = 0;
    let totalConfScore = 0;

    for (const d of declarations) {
      const risk = d.risk_score ?? 0;
      totalRisk += risk;

      for (const bucket of riskBuckets) {
        if (risk >= bucket.min && risk <= bucket.max) { bucket.count++; break; }
      }

      for (const f of d.flagged_fields ?? []) {
        flaggedFreq[f] = (flaggedFreq[f] ?? 0) + 1;
      }

      const dt = d.document_type ?? "commercial_invoice";
      riskByDoc[dt] = (riskByDoc[dt] ?? 0) + risk;
      countByDoc[dt] = (countByDoc[dt] ?? 0) + 1;

      const fields = d.extracted_fields ?? {};
      for (const [, val] of Object.entries(fields)) {
        if (val) totalExtracted++; else totalMissing++;
      }

      totalConfScore += { high: 0.85, medium: 0.5, low: 0.1 }[d.confidence_badge ?? "medium"];
    }

    const n = declarations.length || 1;
    const avgRisk = Math.round(totalRisk / n);
    const avgConf = Math.round((totalConfScore / n) * 100);

    const topFlagged = Object.entries(flaggedFreq)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 7)
      .map(([raw, count]) => ({
        raw,
        label: raw.startsWith("missing:")
          ? `Missing: ${FIELD_LABELS[raw.replace("missing:", "")] ?? raw.replace("missing:", "")}`
          : raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        count,
      }));

    const riskByDocAvg = Object.entries(riskByDoc)
      .map(([dt, total]) => ({ dt, label: DOC_LABELS[dt] ?? dt, avg: Math.round(total / countByDoc[dt]) }))
      .sort((a, b) => b.avg - a.avg);

    const maxBucket = Math.max(...riskBuckets.map((b) => b.count), 1);
    const extractionRate = totalExtracted + totalMissing
      ? Math.round((totalExtracted / (totalExtracted + totalMissing)) * 100)
      : 0;

    return { riskBuckets, maxBucket, topFlagged, riskByDocAvg, avgRisk, avgConf, totalExtracted, totalMissing, extractionRate };
  }, [declarations]);

  const hasData = declarations.length > 0;

  return (
    <div className="space-y-5">
      {/* Pipeline KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KPICard label="Avg Risk Score" value={hasData ? `${data.avgRisk}%` : "—"} colour="text-yellow-400" />
        <KPICard label="Avg OCR Confidence" value={hasData ? `${data.avgConf}%` : "—"} colour="text-blue-400" />
        <KPICard label="Fields Extracted" value={data.totalExtracted} colour="text-emerald-400" />
        <KPICard label="Fields Missing" value={data.totalMissing} colour="text-red-400" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Risk score distribution */}
        <SectionCard title="Risk Score Distribution">
          {!hasData ? (
            <Empty />
          ) : (
            data.riskBuckets.map((bucket) => {
              const pct = Math.round((bucket.count / declarations.length) * 100);
              const barW = Math.round((bucket.count / data.maxBucket) * 100);
              return (
                <div key={bucket.label} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-300">{bucket.label}</span>
                    <span className={bucket.textColour}>{bucket.count} scan{bucket.count !== 1 ? "s" : ""} · {pct}%</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2.5">
                    <div className={`h-2.5 rounded-full transition-all ${bucket.colour}`} style={{ width: `${barW}%` }} />
                  </div>
                </div>
              );
            })
          )}
        </SectionCard>

        {/* Most flagged fields */}
        <SectionCard title="Most Flagged Fields">
          {data.topFlagged.length === 0 ? (
            <p className="text-sm text-emerald-400">No flagged fields detected — great quality!</p>
          ) : (
            <div className="space-y-2">
              {data.topFlagged.map(({ raw, label, count }, i) => (
                <div key={raw} className="flex items-center gap-3">
                  <span className="w-5 text-xs text-gray-600 font-mono shrink-0">{i + 1}.</span>
                  <span className="flex-1 text-sm text-gray-300 truncate">{label}</span>
                  <span className="text-xs bg-red-900/40 text-red-400 border border-red-800 px-2 py-0.5 rounded-full shrink-0">
                    {count}×
                  </span>
                </div>
              ))}
            </div>
          )}
        </SectionCard>

        {/* Avg risk by document type */}
        <SectionCard title="Avg Risk Score by Document Type">
          {data.riskByDocAvg.length === 0 ? (
            <Empty />
          ) : (
            data.riskByDocAvg.map(({ dt, label, avg }) => {
              const barColour = avg < 30 ? "bg-emerald-500" : avg < 70 ? "bg-yellow-500" : "bg-red-500";
              const textColour = avg < 30 ? "text-emerald-400" : avg < 70 ? "text-yellow-400" : "text-red-400";
              return (
                <div key={dt} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-300">{label}</span>
                    <span className={textColour}>{avg}% avg</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div className={`h-2 rounded-full transition-all ${barColour}`} style={{ width: `${avg}%` }} />
                  </div>
                </div>
              );
            })
          )}
        </SectionCard>

        {/* Field extraction quality */}
        <SectionCard title="Field Extraction Quality">
          {!hasData ? (
            <Empty />
          ) : (
            <div className="space-y-4">
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-300">Successfully Extracted</span>
                    <span className="text-emerald-400">{data.totalExtracted} fields</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div className="h-2 rounded-full bg-emerald-500 transition-all" style={{ width: `${data.extractionRate}%` }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-300">Not Detected / Missing</span>
                    <span className="text-red-400">{data.totalMissing} fields</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div className="h-2 rounded-full bg-red-500 transition-all" style={{ width: `${100 - data.extractionRate}%` }} />
                  </div>
                </div>
              </div>
              <div className="pt-1 border-t border-gray-800 text-xs text-gray-500">
                {data.extractionRate}% extraction success rate · {declarations.length} scan{declarations.length !== 1 ? "s" : ""} analysed
              </div>
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}

function KPICard({ label, value, colour }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-4">
      <div className={`text-3xl font-bold ${colour}`}>{value}</div>
      <div className="text-xs text-gray-400 mt-1 leading-tight">{label}</div>
    </div>
  );
}

function SectionCard({ title, children }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{title}</h3>
      {children}
    </div>
  );
}

function Empty() {
  return <p className="text-xs text-gray-600">No data yet — waiting for scans.</p>;
}
