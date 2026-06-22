import { useEffect, useState } from "react";
import { FieldEditor } from "./FieldEditor";
import { CeisaModal } from "./CeisaModal";
import { ShapExplainer } from "./ShapExplainer";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const DOC_LABELS = {
  commercial_invoice: "Commercial Invoice",
  bill_of_lading: "Bill of Lading",
  packing_list: "Packing List",
};

function isPdf(b64) { return b64?.startsWith("JVBERi0"); }
function mime(b64) {
  if (!b64) return "image/jpeg";
  if (b64.startsWith("/9j/")) return "image/jpeg";
  if (b64.startsWith("iVBORw")) return "image/png";
  return "image/jpeg";
}

export function DetailPanel({ declaration, token, onClose, onUpdate, onReview, onSubmit, onReprocess }) {
  const [imageData, setImageData] = useState(null);
  const [imageFetched, setImageFetched] = useState(false);
  const [ceisaOpen, setCeisaOpen] = useState(false);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [note, setNote] = useState("");

  const id = declaration.id;
  const riskBadge = declaration.risk_badge ?? "yellow";
  const riskScore = declaration.risk_score ?? 0;
  const confidence = declaration.confidence_badge ?? "medium";
  const flagged = declaration.flagged_fields ?? [];
  const fields = declaration.extracted_fields ?? {};
  const reviewStatus = declaration.review_status ?? "pending";

  useEffect(() => {
    setImageData(null);
    setImageFetched(false);
    setNote(declaration.review_note ?? "");
  }, [declaration.id]);

  useEffect(() => {
    if (imageFetched || !token) return;
    setImageFetched(true);
    fetch(`${API}/declarations/${id}/image`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { if (data?.image_data) setImageData(data.image_data); })
      .catch(() => {});
  }, [id, token, imageFetched]);

  const handleReview = async (status) => {
    setReviewLoading(true);
    try {
      await onReview(id, status, note);
    } finally {
      setReviewLoading(false);
    }
  };

  const riskBarColour = riskBadge === "green" ? "bg-emerald-500" : riskBadge === "red" ? "bg-red-500" : "bg-yellow-500";
  const riskTextColour = riskBadge === "green" ? "text-emerald-400" : riskBadge === "red" ? "text-red-400" : "text-yellow-400";

  return (
    <div className="fixed inset-0 z-30 flex">
      {/* Backdrop */}
      <div className="flex-1 bg-black/50" onClick={onClose} />

      {/* Panel */}
      <div className="w-[480px] bg-gray-900 border-l border-gray-800 flex flex-col h-full overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800 shrink-0">
          <div>
            <div className="font-semibold text-white">{DOC_LABELS[declaration.document_type] ?? "Document"}</div>
            <div className="text-xs text-gray-500 mt-0.5">
              {declaration.scanned_at ? new Date(declaration.scanned_at).toLocaleString() : "—"}
              {declaration.operator_id ? ` · ${declaration.operator_id}` : ""}
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors p-1">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {/* Document image */}
          <div className="px-5 pt-4 pb-3">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Document</div>
            {imageData ? (
              isPdf(imageData) ? (
                <div className="flex flex-col items-center gap-2 bg-gray-800 rounded-xl py-8 border border-gray-700">
                  <svg className="w-10 h-10 text-gray-500" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                  </svg>
                  <span className="text-xs text-gray-500">PDF Document</span>
                  <a href={`data:application/pdf;base64,${imageData}`} download={`declaration-${id}.pdf`}
                    className="text-xs text-blue-400 hover:text-blue-300 underline">Download PDF</a>
                </div>
              ) : (
                <img src={`data:${mime(imageData)};base64,${imageData}`} alt="Document"
                  className="w-full rounded-xl border border-gray-700 object-contain max-h-56" />
              )
            ) : (
              <div className="flex items-center justify-center bg-gray-800 rounded-xl py-8 border border-gray-700">
                <span className="text-xs text-gray-600">{imageFetched ? "No image stored" : "Loading…"}</span>
              </div>
            )}
          </div>

          {/* Risk + Confidence */}
          <div className="px-5 pb-4 grid grid-cols-2 gap-3">
            <div className="bg-gray-800 rounded-xl p-3">
              <div className="text-xs text-gray-500 mb-1">Risk Score</div>
              <div className={`text-2xl font-bold ${riskTextColour}`}>{riskScore}%</div>
              <div className="mt-2 w-full bg-gray-700 rounded-full h-1.5">
                <div className={`h-1.5 rounded-full ${riskBarColour}`} style={{ width: `${riskScore}%` }} />
              </div>
            </div>
            <div className="bg-gray-800 rounded-xl p-3">
              <div className="text-xs text-gray-500 mb-1">OCR Confidence</div>
              <div className={`text-2xl font-bold ${confidence === "high" ? "text-blue-400" : confidence === "low" ? "text-red-400" : "text-orange-400"}`}>
                {confidence.toUpperCase()}
              </div>
              <div className="text-xs text-gray-600 mt-1">Tesseract OCR</div>
            </div>
          </div>

          {/* SHAP Explainer */}
          {declaration.shap_values?.length > 0 && (
            <div className="px-5 pb-4">
              <div className="bg-gray-800 rounded-xl p-4">
                <ShapExplainer
                  shapValues={declaration.shap_values}
                  riskBadge={riskBadge}
                  riskScore={riskScore}
                />
              </div>
            </div>
          )}

          {/* Extraction method badge */}
          {declaration.extraction_method && (
            <div className="px-5 pb-3 flex items-center gap-2">
              <span className="text-xs text-gray-500">Extraction engine:</span>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
                declaration.extraction_method === "ner"
                  ? "bg-blue-900/30 text-blue-400 border-blue-800"
                  : declaration.extraction_method === "ner+regex"
                  ? "bg-purple-900/30 text-purple-400 border-purple-800"
                  : "bg-gray-800 text-gray-400 border-gray-700"
              }`}>
                {declaration.extraction_method === "ner" ? "spaCy NER (Deep Learning)"
                  : declaration.extraction_method === "ner+regex" ? "NER + Regex Hybrid"
                  : "Regex"}
              </span>
            </div>
          )}

          {/* Flagged */}
          {flagged.length > 0 && (
            <div className="px-5 pb-4">
              <div className="bg-red-900/20 border border-red-800/50 rounded-xl p-3 space-y-1">
                <div className="text-xs font-semibold text-red-400 mb-2">! Flagged Issues</div>
                {flagged.map((f) => (
                  <div key={f} className="text-xs text-red-300">{f.replace("missing:", "Missing: ")}</div>
                ))}
              </div>
            </div>
          )}

          {/* Extracted fields */}
          <div className="px-5 pb-4">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Extracted Fields</div>
            <div className="bg-gray-800 rounded-xl p-3">
              <FieldEditor fields={fields} onUpdate={(fieldName, value) => onUpdate(id, fieldName, value)} />
            </div>
          </div>

          {/* Review section */}
          <div className="px-5 pb-6">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Manager Review</div>
            <div className="bg-gray-800 rounded-xl p-4 space-y-3">
              {/* Current status */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">Status:</span>
                <ReviewStatusBadge status={reviewStatus} />
                {declaration.reviewed_by && (
                  <span className="text-xs text-gray-600">by {declaration.reviewed_by}</span>
                )}
              </div>

              {reviewStatus === "pending" && (
                <>
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="Add a review note (optional)…"
                    rows={2}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-300 placeholder-gray-600 focus:outline-none focus:border-blue-500 resize-none"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleReview("approved")}
                      disabled={reviewLoading}
                      className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg text-sm font-semibold text-white transition-colors"
                    >
                      ✓ Approve
                    </button>
                    <button
                      onClick={() => handleReview("rejected")}
                      disabled={reviewLoading}
                      className="flex-1 py-2 bg-red-700 hover:bg-red-600 disabled:opacity-50 rounded-lg text-sm font-semibold text-white transition-colors"
                    >
                      ✕ Reject
                    </button>
                  </div>
                </>
              )}

              {reviewStatus !== "pending" && (
                <>
                  {declaration.review_note && (
                    <div className="text-xs text-gray-400 italic">"{declaration.review_note}"</div>
                  )}
                  <button
                    onClick={() => handleReview("pending")}
                    className="text-xs text-gray-500 hover:text-gray-300 underline transition-colors"
                  >
                    Reset to pending
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-gray-800 shrink-0 space-y-2">
          <button
            onClick={() => setCeisaOpen(true)}
            disabled={!declaration.ceisa_ready}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-600 rounded-lg text-sm font-semibold transition-colors"
          >
            {declaration.ceisa_ready ? "Submit to CEISA →" : "Not ready for CEISA submission"}
          </button>
          {onReprocess && (
            <button
              onClick={() => onReprocess(id)}
              className="w-full py-2 bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white rounded-lg text-xs font-medium transition-colors"
            >
              ↻ Re-run OCR
            </button>
          )}
        </div>
      </div>

      {ceisaOpen && (
        <CeisaModal declarationId={id} onClose={() => setCeisaOpen(false)} onSubmit={onSubmit} />
      )}
    </div>
  );
}

function ReviewStatusBadge({ status }) {
  const cfg = {
    pending: "bg-yellow-900/40 text-yellow-400 border-yellow-700",
    approved: "bg-emerald-900/40 text-emerald-400 border-emerald-700",
    rejected: "bg-red-900/40 text-red-400 border-red-700",
  }[status] ?? "bg-gray-800 text-gray-400 border-gray-700";

  const label = { pending: "Pending", approved: "Approved", rejected: "Rejected" }[status] ?? status;

  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${cfg}`}>{label}</span>
  );
}
