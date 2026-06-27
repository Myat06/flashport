import { useState } from "react";

const DOC_LABELS = {
  commercial_invoice: "Commercial Invoice",
  bill_of_lading: "Bill of Lading",
  packing_list: "Packing List",
};

const FILTERS = [
  { key: "all", label: "All" },
  { key: "pending", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
];

function RiskPill({ badge, score }) {
  const cfg = {
    green: "text-emerald-400 bg-emerald-900/30 border-emerald-800",
    yellow: "text-yellow-400 bg-yellow-900/30 border-yellow-800",
    red: "text-red-400 bg-red-900/30 border-red-800",
  }[badge] ?? "text-gray-400 bg-gray-800 border-gray-700";
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border ${cfg}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {score ?? 0}%
    </span>
  );
}

function ReviewPill({ status }) {
  const cfg = {
    pending: "text-yellow-400 bg-yellow-900/20 border-yellow-800",
    approved: "text-emerald-400 bg-emerald-900/20 border-emerald-800",
    rejected: "text-red-400 bg-red-900/20 border-red-800",
  }[status] ?? "text-gray-400 bg-gray-800 border-gray-700";
  const icon = { pending: "●", approved: "✓", rejected: "✕" }[status] ?? "●";
  const label = { pending: "Pending", approved: "Approved", rejected: "Rejected" }[status] ?? status;
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border ${cfg}`}>
      {icon} {label}
    </span>
  );
}

function ConfPill({ badge }) {
  const cfg = {
    high: "text-blue-400",
    medium: "text-orange-400",
    low: "text-red-400",
  }[badge] ?? "text-gray-400";
  return <span className={`text-xs font-medium ${cfg}`}>{(badge ?? "—").toUpperCase()}</span>;
}

export function DeclarationTable({ declarations, onSelect, selectedIds = new Set(), onSelectIds }) {
  const [filter, setFilter]   = useState("all");
  const [search, setSearch]   = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo]     = useState("");

  const toggleSelect = (e, id) => {
    e.stopPropagation();
    const next = new Set(selectedIds);
    next.has(id) ? next.delete(id) : next.add(id);
    onSelectIds?.(next);
  };

  const clearDates = () => { setDateFrom(""); setDateTo(""); };

  const filtered = declarations.filter((d) => {
    const status = d.review_status ?? "pending";
    if (filter !== "all" && status !== filter) return false;
    if (search) {
      const q   = search.toLowerCase();
      const doc = DOC_LABELS[d.document_type]?.toLowerCase() ?? "";
      const op  = (d.operator_id ?? "").toLowerCase();
      if (!doc.includes(q) && !op.includes(q)) return false;
    }
    if (dateFrom || dateTo) {
      const ts = d.scanned_at ? new Date(d.scanned_at) : null;
      if (!ts) return false;
      if (dateFrom && ts < new Date(dateFrom))                   return false;
      if (dateTo   && ts > new Date(dateTo + "T23:59:59"))       return false;
    }
    return true;
  });

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      {/* Table toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 gap-4">
        <div className="flex gap-1">
          {FILTERS.map(({ key, label }) => {
            const count = key === "all"
              ? declarations.length
              : declarations.filter((d) => (d.review_status ?? "pending") === key).length;
            return (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  filter === key
                    ? "bg-blue-600 text-white"
                    : "text-gray-400 hover:text-white hover:bg-gray-800"
                }`}
              >
                {label}
                <span className={`ml-1.5 px-1.5 py-0.5 rounded-full text-xs ${filter === key ? "bg-blue-500" : "bg-gray-700 text-gray-400"}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
        <div className="flex items-center gap-2">
          {/* Date range */}
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            title="From date"
            className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-blue-500 w-32 [color-scheme:dark]"
          />
          <span className="text-gray-600 text-xs">–</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            title="To date"
            className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-blue-500 w-32 [color-scheme:dark]"
          />
          {(dateFrom || dateTo) && (
            <button onClick={clearDates} className="text-xs text-gray-500 hover:text-gray-300 transition-colors">✕</button>
          )}
          {/* Search */}
          <input
            type="text"
            placeholder="Search document or operator…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-gray-300 placeholder-gray-600 focus:outline-none focus:border-blue-500 w-48"
          />
        </div>
      </div>

      {/* Header row */}
      <div className="grid grid-cols-[32px_2fr_1.2fr_1.4fr_80px_90px_100px_28px] gap-4 px-4 py-2.5 border-b border-gray-800 text-xs font-semibold text-gray-500 uppercase tracking-wide">
        <span />
        <span>Document</span>
        <span>Operator</span>
        <span>Date</span>
        <span>Risk</span>
        <span>Confidence</span>
        <span>Status</span>
        <span />
      </div>

      {/* Rows */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-600">
          <div className="text-4xl mb-3">📄</div>
          <div className="text-sm">{declarations.length === 0 ? "No declarations yet — waiting for field scans." : "No results match this filter."}</div>
        </div>
      ) : (
        <div className="divide-y divide-gray-800/60">
          {filtered.map((d) => {
            const reviewStatus = d.review_status ?? "pending";
            const leftBorder = {
              approved: "border-l-2 border-l-emerald-500",
              rejected: "border-l-2 border-l-red-500",
              pending: "border-l-2 border-l-yellow-500/40",
            }[reviewStatus] ?? "";

            return (
              <div
                key={d.id}
                onClick={() => onSelect(d)}
                className={`grid grid-cols-[32px_2fr_1.2fr_1.4fr_80px_90px_100px_28px] gap-4 px-4 py-3.5 cursor-pointer hover:bg-gray-800/50 transition-colors items-center ${leftBorder}`}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.has(d.id)}
                  onChange={(e) => toggleSelect(e, d.id)}
                  onClick={(e) => e.stopPropagation()}
                  className="w-4 h-4 rounded border-gray-600 bg-gray-800 accent-blue-600 cursor-pointer"
                />
                <div>
                  <div className="text-sm font-medium text-white">{DOC_LABELS[d.document_type] ?? d.document_type}</div>
                  <div className="text-xs text-gray-600 mt-0.5 font-mono">{String(d.id).slice(0, 8)}…</div>
                </div>
                <div className="text-sm text-gray-300">{d.operator_id ?? <span className="text-gray-600 italic">—</span>}</div>
                <div className="text-xs text-gray-400">
                  {d.scanned_at ? new Date(d.scanned_at).toLocaleString() : "—"}
                </div>
                <div><RiskPill badge={d.risk_badge} score={d.risk_score} /></div>
                <div><ConfPill badge={d.confidence_badge} /></div>
                <div><ReviewPill status={reviewStatus} /></div>
                <div className="text-gray-600">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                  </svg>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
