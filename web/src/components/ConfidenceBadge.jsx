export function ConfidenceBadge({ badge }) {
  const colours = {
    high: "bg-blue-900 text-blue-300 border-blue-700",
    medium: "bg-orange-900 text-orange-300 border-orange-700",
    low: "bg-red-900 text-red-300 border-red-700",
  };
  const icons = { high: "✓", medium: "~", low: "!" };
  const cls = colours[badge] ?? colours.medium;

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full border text-xs font-semibold uppercase ${cls}`}>
      {icons[badge]} OCR {badge}
    </span>
  );
}
