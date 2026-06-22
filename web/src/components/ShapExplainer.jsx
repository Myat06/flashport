const BADGE_COLOURS = {
  green:  { bar: "bg-emerald-500", text: "text-emerald-400", light: "bg-emerald-900/20" },
  yellow: { bar: "bg-yellow-500",  text: "text-yellow-400",  light: "bg-yellow-900/20" },
  red:    { bar: "bg-red-500",     text: "text-red-400",     light: "bg-red-900/20" },
};

export function ShapExplainer({ shapValues = [], riskBadge = "yellow", riskScore = 0 }) {
  if (!shapValues || shapValues.length === 0) return null;

  // Sort by absolute SHAP value descending, take top 8
  const sorted = [...shapValues]
    .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
    .slice(0, 8);

  const maxAbs = Math.max(...sorted.map((s) => Math.abs(s.shap_value)), 0.001);
  const colours = BADGE_COLOURS[riskBadge] ?? BADGE_COLOURS.yellow;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
          AI Explanation (SHAP)
        </div>
        <div className={`text-xs font-semibold px-2 py-0.5 rounded-full ${colours.light} ${colours.text}`}>
          Risk: {riskScore}%
        </div>
      </div>

      <div className="text-xs text-gray-500 leading-relaxed">
        Factors driving this risk score — red bars increase risk, green bars reduce it:
      </div>

      <div className="space-y-2">
        {sorted.map((s) => {
          const pct = Math.abs(s.shap_value) / maxAbs * 100;
          const isIncrease = s.shap_value > 0;
          const barColour = isIncrease ? "bg-red-500" : "bg-emerald-500";
          const valColour = isIncrease ? "text-red-400" : "text-emerald-400";
          const sign = isIncrease ? "+" : "";

          return (
            <div key={s.feature} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-300 truncate max-w-[65%]">{s.label}</span>
                <span className={`font-mono font-semibold ${valColour}`}>
                  {sign}{s.shap_value.toFixed(3)}
                </span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-1.5 rounded-full transition-all ${barColour}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="pt-1 border-t border-gray-800 text-xs text-gray-600">
        SHAP (SHapley Additive exPlanations) — higher absolute value = stronger influence on score
      </div>
    </div>
  );
}
