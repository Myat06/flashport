import { useState } from "react";

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

export function FieldEditor({ fields = {}, onUpdate }) {
  const [editing, setEditing] = useState(null);
  const [draft, setDraft] = useState("");

  const startEdit = (key, value) => {
    setEditing(key);
    setDraft(value ?? "");
  };

  const commit = (key) => {
    onUpdate(key, draft);
    setEditing(null);
  };

  return (
    <div className="space-y-2">
      {Object.entries(FIELD_LABELS).map(([key, label]) => {
        const value = fields[key];
        const missing = !value;
        return (
          <div key={key} className="flex items-start gap-2">
            <span className="w-32 shrink-0 text-xs text-gray-400 pt-1">{label}</span>
            {editing === key ? (
              <div className="flex flex-1 gap-1">
                <input
                  className="flex-1 bg-gray-800 border border-blue-500 rounded px-2 py-0.5 text-sm focus:outline-none"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && commit(key)}
                  autoFocus
                />
                <button
                  onClick={() => commit(key)}
                  className="px-2 py-0.5 bg-blue-600 rounded text-xs hover:bg-blue-500"
                >
                  Save
                </button>
                <button
                  onClick={() => setEditing(null)}
                  className="px-2 py-0.5 bg-gray-700 rounded text-xs hover:bg-gray-600"
                >
                  ✕
                </button>
              </div>
            ) : (
              <button
                onClick={() => startEdit(key, value)}
                className={`flex-1 text-left text-sm px-2 py-0.5 rounded hover:bg-gray-800 transition-colors ${
                  missing ? "text-red-400 italic" : "text-gray-100"
                }`}
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
