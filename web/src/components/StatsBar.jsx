export function StatsBar({ declarations }) {
  const total = declarations.length;
  const pending = declarations.filter((d) => (d.review_status ?? "pending") === "pending").length;
  const approved = declarations.filter((d) => d.review_status === "approved").length;
  const rejected = declarations.filter((d) => d.review_status === "rejected").length;
  const ceisaReady = declarations.filter((d) => d.ceisa_ready).length;

  const stats = [
    { label: "Total", value: total, colour: "text-white", sub: "declarations", dot: "bg-gray-400" },
    { label: "Pending Review", value: pending, colour: "text-yellow-400", sub: "need action", dot: "bg-yellow-400" },
    { label: "Approved", value: approved, colour: "text-emerald-400", sub: "cleared", dot: "bg-emerald-400" },
    { label: "Rejected", value: rejected, colour: "text-red-400", sub: "flagged", dot: "bg-red-400" },
    { label: "CEISA Ready", value: ceisaReady, colour: "text-blue-400", sub: "ready to submit", dot: "bg-blue-400" },
  ];

  return (
    <div className="grid grid-cols-5 gap-4 mb-6">
      {stats.map(({ label, value, colour, sub, dot }) => (
        <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-4">
          <div className="flex items-center gap-2 mb-2">
            <span className={`w-2 h-2 rounded-full ${dot}`} />
            <span className="text-xs text-gray-500 font-medium uppercase tracking-wide">{label}</span>
          </div>
          <div className={`text-3xl font-bold ${colour}`}>{value}</div>
          <div className="text-xs text-gray-600 mt-0.5">{sub}</div>
        </div>
      ))}
    </div>
  );
}
