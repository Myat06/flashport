import { useState } from "react";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { FieldEditor } from "./FieldEditor";
import { RiskBadge } from "./RiskBadge";
import { CeisaModal } from "./CeisaModal";

const DOC_LABELS = {
  commercial_invoice: "Commercial Invoice",
  bill_of_lading: "Bill of Lading",
  packing_list: "Packing List",
};

export function DeclarationCard({ declaration, onUpdate, onSubmit }) {
  const [expanded, setExpanded] = useState(false);
  const [ceisaOpen, setCeisaOpen] = useState(false);

  const id = declaration.declaration_id ?? declaration.id;
  const riskBadge = declaration.risk_badge ?? "yellow";
  const riskScore = declaration.risk_score ?? 0;
  const confidenceBadge = declaration.confidence_badge ?? "medium";
  const fields = declaration.extracted_fields ?? {};
  const flagged = declaration.flagged_fields ?? [];
  const docType = declaration.document_type ?? "commercial_invoice";
  const scannedAt = declaration.scanned_at
    ? new Date(declaration.scanned_at).toLocaleString("id-ID")
    : "—";

  const borderColour = {
    green: "border-l-emerald-500",
    yellow: "border-l-yellow-500",
    red: "border-l-red-500",
  }[riskBadge];

  return (
    <>
      <div className={`bg-gray-900 border border-gray-800 border-l-4 ${borderColour} rounded-lg overflow-hidden`}>
        {/* Header row */}
        <div
          className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-800/50 transition-colors"
          onClick={() => setExpanded((v) => !v)}
        >
          <div className="flex-1 min-w-0">
            <div className="font-medium text-sm truncate">{DOC_LABELS[docType]}</div>
            <div className="text-xs text-gray-500 truncate">{scannedAt} · {declaration.operator_id ?? "Field Operator"}</div>
          </div>
          <ConfidenceBadge badge={confidenceBadge} />
          <RiskBadge score={riskScore} badge={riskBadge} />
          <span className="text-gray-500 text-sm">{expanded ? "▲" : "▼"}</span>
        </div>

        {expanded && (
          <div className="border-t border-gray-800">
            {/* Split-screen */}
            <div className="grid grid-cols-2 divide-x divide-gray-800">
              {/* Left: field data */}
              <div className="p-4">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Extracted Fields</h3>
                <FieldEditor
                  fields={fields}
                  onUpdate={(fieldName, value) => onUpdate(id, fieldName, value)}
                />
              </div>

              {/* Right: AI analysis */}
              <div className="p-4 space-y-4">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">AI Analysis</h3>

                <div>
                  <div className="text-xs text-gray-500 mb-1">Risk Score</div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        riskBadge === "green" ? "bg-emerald-500" :
                        riskBadge === "yellow" ? "bg-yellow-500" : "bg-red-500"
                      }`}
                      style={{ width: `${riskScore}%` }}
                    />
                  </div>
                  <div className="text-xs text-gray-400 mt-1">{riskScore}% risk</div>
                </div>

                {flagged.length > 0 && (
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Flagged Issues</div>
                    <ul className="space-y-1">
                      {flagged.map((f) => (
                        <li key={f} className="text-xs text-red-400 flex items-start gap-1">
                          <span className="mt-0.5">⚠</span> {f.replace("missing:", "Missing field: ")}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="pt-2">
                  <button
                    onClick={() => setCeisaOpen(true)}
                    className="w-full py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-semibold transition-colors"
                  >
                    Submit to CEISA →
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {ceisaOpen && (
        <CeisaModal
          declarationId={id}
          onClose={() => setCeisaOpen(false)}
          onSubmit={onSubmit}
        />
      )}
    </>
  );
}
