import { useState } from "react";

// Fallback static labels for the 11 built-in fields when fieldDefs not yet loaded
const BUILTIN_LABELS = {
  hs_code: "HS Code", invoice_value: "Invoice Value", container_id: "Container ID",
  importer: "Importer", exporter: "Exporter", net_weight: "Net Weight",
  gross_weight: "Gross Weight", vessel_name: "Vessel Name", port_of_origin: "Port of Origin",
  invoice_number: "Invoice No.", carton_count: "Carton Count",
};

function ValidationIcon({ vr }) {
  if (!vr) return null;
  if (vr.is_valid) return <span title="Valid" className="text-emerald-400 text-xs shrink-0">✓</span>;
  const color = vr.priority === "critical" ? "text-red-400"
    : vr.priority === "important" ? "text-orange-400" : "text-yellow-400";
  return <span title={vr.message ?? "Invalid"} className={`${color} text-xs shrink-0 cursor-help`}>⚠</span>;
}

export function FieldEditor({ fields = {}, validationResults = [], fieldDefs = [], onUpdate }) {
  const [editing, setEditing] = useState(null);
  const [draft, setDraft]     = useState("");

  const vrMap = Object.fromEntries(validationResults.map(r => [r.field_name, r]));

  // Build ordered label map: prefer fieldDefs (dynamic), fall back to BUILTIN_LABELS,
  // then include any extra keys found in `fields` that aren't in either.
  const orderedKeys = (() => {
    if (fieldDefs.length > 0) {
      const defsKeys  = fieldDefs.filter(fd => fd.is_active).map(fd => fd.field_key);
      const extraKeys = Object.keys(fields).filter(k => !defsKeys.includes(k));
      return [...defsKeys, ...extraKeys];
    }
    const builtinKeys = Object.keys(BUILTIN_LABELS);
    const extraKeys   = Object.keys(fields).filter(k => !builtinKeys.includes(k));
    return [...builtinKeys, ...extraKeys];
  })();

  const labelFor = (key) => {
    const fd = fieldDefs.find(f => f.field_key === key);
    return fd?.display_label ?? BUILTIN_LABELS[key] ?? key;
  };

  const startEdit = (key, value) => { setEditing(key); setDraft(value ?? ""); };
  const commit    = (key) => { onUpdate(key, draft); setEditing(null); };

  return (
    <div className="space-y-2">
      {orderedKeys.map(key => {
        const value   = fields[key];
        const vr      = vrMap[key];
        const missing = !value;
        const invalid = vr && !vr.is_valid;
        const label   = labelFor(key);

        const valueCls = missing ? "text-red-400 italic"
          : invalid ? (vr.priority === "critical" ? "text-red-300"
              : vr.priority === "important" ? "text-orange-300" : "text-yellow-300")
          : "text-gray-100";

        return (
          <div key={key} className="flex items-start gap-2">
            <span className="w-32 shrink-0 text-xs text-gray-400 pt-1 truncate" title={label}>{label}</span>
            <ValidationIcon vr={vr} />
            {editing === key ? (
              <div className="flex flex-1 gap-1">
                <input
                  className="flex-1 bg-gray-800 border border-blue-500 rounded px-2 py-0.5 text-sm focus:outline-none"
                  value={draft}
                  onChange={e => setDraft(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && commit(key)}
                  autoFocus
                />
                <button onClick={() => commit(key)}
                  className="px-2 py-0.5 bg-blue-600 rounded text-xs hover:bg-blue-500">Save</button>
                <button onClick={() => setEditing(null)}
                  className="px-2 py-0.5 bg-gray-700 rounded text-xs hover:bg-gray-600">✕</button>
              </div>
            ) : (
              <button
                onClick={() => startEdit(key, value)}
                className={`flex-1 text-left text-sm px-2 py-0.5 rounded hover:bg-gray-800 transition-colors ${valueCls}`}
                title={invalid ? vr.message : undefined}
              >
                {value ?? "— missing —"}
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
