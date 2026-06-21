export function RiskBadge({ score, badge }) {
  const colours = {
    green: "bg-emerald-900 text-emerald-300 border-emerald-700",
    yellow: "bg-yellow-900 text-yellow-300 border-yellow-700",
    red: "bg-red-900 text-red-300 border-red-700",
  };
  const labels = { green: "Jalur Hijau", yellow: "Jalur Kuning", red: "Jalur Merah" };
  const cls = colours[badge] ?? colours.yellow;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${cls}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {labels[badge] ?? badge} · {score}%
    </span>
  );
}
