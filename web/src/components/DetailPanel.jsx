import { useEffect, useCallback, useRef, useState } from "react";
import { FieldEditor } from "./FieldEditor";
import { CeisaModal } from "./CeisaModal";
import { ShapExplainer } from "./ShapExplainer";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const DOC_LABELS = {
  commercial_invoice: "Commercial Invoice",
  bill_of_lading: "Bill of Lading",
  packing_list: "Packing List",
};

const FIELD_LABELS = {
  hs_code: "HS Code", invoice_value: "Invoice Value", container_id: "Container ID",
  importer: "Importer", exporter: "Exporter", net_weight: "Net Weight",
  gross_weight: "Gross Weight", invoice_number: "Invoice No.", carton_count: "Cartons",
  vessel_name: "Vessel", port_of_origin: "Port of Origin",
};

function isPdf(b64) { return b64?.startsWith("JVBERi0"); }
function mime(b64) {
  if (!b64) return "image/jpeg";
  if (b64.startsWith("/9j/")) return "image/jpeg";
  if (b64.startsWith("iVBORw")) return "image/png";
  return "image/jpeg";
}

// ── Colour helpers ─────────────────────────────────────────────────────────────
const BOX_STYLES = {
  critical: {
    valid:   { stroke: "#22c55e", strokeWidth: 3, dash: "none" },
    invalid: { stroke: "#ef4444", strokeWidth: 3, dash: "none" },
    missing: { stroke: "#ef4444", strokeWidth: 3, dash: "6 3" },
  },
  important: {
    valid:   { stroke: "#22c55e", strokeWidth: 2, dash: "none" },
    invalid: { stroke: "#f97316", strokeWidth: 2, dash: "none" },
    missing: { stroke: "#f97316", strokeWidth: 2, dash: "5 3" },
  },
  optional: {
    valid:   { stroke: "#22c55e", strokeWidth: 1.5, dash: "none" },
    invalid: { stroke: "#eab308", strokeWidth: 1.5, dash: "4 3" },
    missing: { stroke: "#eab308", strokeWidth: 1.5, dash: "4 3" },
  },
};

const LABEL_FILL = {
  critical: { valid: "#16a34a", invalid: "#dc2626", missing: "#dc2626" },
  important: { valid: "#16a34a", invalid: "#ea580c", missing: "#ea580c" },
  optional:  { valid: "#16a34a", invalid: "#ca8a04", missing: "#ca8a04" },
};

function FieldBox({ vr, imgW, imgH }) {
  const { field_name, value, is_valid, priority, message, bbox } = vr;
  if (!bbox) return null;

  const state  = !value ? "missing" : is_valid ? "valid" : "invalid";
  const style  = BOX_STYLES[priority]?.[state] ?? BOX_STYLES.optional.invalid;
  const fill   = LABEL_FILL[priority]?.[state] ?? "#ca8a04";
  const label  = FIELD_LABELS[field_name] ?? field_name;
  const icon   = state === "valid" ? "✓" : "⚠";
  const tag    = `${icon} ${label}`;
  const tagW   = tag.length * 6.5 + 10;

  return (
    <g>
      <rect
        x={bbox.x} y={bbox.y} width={bbox.w} height={bbox.h}
        fill={state === "invalid" || state === "missing" ? `${style.stroke}15` : "transparent"}
        stroke={style.stroke}
        strokeWidth={style.strokeWidth}
        strokeDasharray={style.dash === "none" ? undefined : style.dash}
        rx={3}
      />
      {/* Label tag in top-left corner of box */}
      <rect
        x={bbox.x} y={bbox.y - 16}
        width={tagW} height={16}
        fill={fill} rx={3}
      />
      <text
        x={bbox.x + 5} y={bbox.y - 4}
        fill="white" fontSize={9} fontWeight="bold"
        fontFamily="system-ui, sans-serif"
      >
        {tag}
      </text>
    </g>
  );
}

function DocSvgOverlay({ imgW, imgH, validationResults }) {
  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none rounded-xl"
      viewBox={`0 0 ${imgW} ${imgH}`}
      preserveAspectRatio="xMidYMid meet"
      style={{ overflow: "visible" }}
    >
      {validationResults.map((vr) => (
        <FieldBox key={vr.field_name} vr={vr} imgW={imgW} imgH={imgH} />
      ))}
    </svg>
  );
}

function DocumentOverlay({ imageData, imgW, imgH, validationResults, onExpand }) {
  const hasBoxes = validationResults.some((r) => r.bbox);

  return (
    <div className="relative w-full group cursor-zoom-in" onClick={onExpand} title="Click to view full size">
      <img
        src={`data:${mime(imageData)};base64,${imageData}`}
        alt="Document"
        className="w-full rounded-xl border border-gray-700 object-contain max-h-72"
        style={{ display: "block" }}
      />
      {hasBoxes && imgW && imgH && (
        <DocSvgOverlay imgW={imgW} imgH={imgH} validationResults={validationResults} />
      )}
      {/* Expand hint */}
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 rounded-lg px-2 py-1 flex items-center gap-1 pointer-events-none">
        <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
        </svg>
        <span className="text-white text-xs font-medium">Full size</span>
      </div>
    </div>
  );
}

function ImageLightbox({ imageData, imgW, imgH, validationResults, showOverlay, onClose }) {
  const onKey = useCallback((e) => { if (e.key === "Escape") onClose(); }, [onClose]);
  useEffect(() => {
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onKey]);

  const hasBoxes = validationResults.some((r) => r.bbox);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Close */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 z-10 bg-white/10 hover:bg-white/20 text-white rounded-full p-2 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
        </svg>
      </button>

      {/* Image container — scroll if image is larger than viewport */}
      <div
        className="relative overflow-auto max-w-[95vw] max-h-[95vh] rounded-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <img
          src={`data:${mime(imageData)};base64,${imageData}`}
          alt="Document"
          className="block rounded-xl border border-white/10"
          style={{ maxWidth: "95vw", maxHeight: "95vh", objectFit: "contain" }}
        />
        {showOverlay && hasBoxes && imgW && imgH && (
          <DocSvgOverlay imgW={imgW} imgH={imgH} validationResults={validationResults} />
        )}
      </div>

      {/* Bottom hint */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-gray-500 text-xs">
        ESC or click outside to close
      </div>
    </div>
  );
}

// ── Validation summary list (fields without bboxes, or all fields) ─────────────
function ValidationSummary({ validationResults }) {
  if (!validationResults?.length) return null;

  const issues = validationResults.filter((r) => !r.is_valid);
  if (!issues.length) return null;

  const priorityOrder = { critical: 0, important: 1, optional: 2 };
  const sorted = [...issues].sort((a, b) =>
    (priorityOrder[a.priority] ?? 3) - (priorityOrder[b.priority] ?? 3)
  );

  return (
    <div className="px-5 pb-4">
      <div className="rounded-xl border border-gray-700 overflow-hidden">
        <div className="px-3 py-2 bg-gray-800 border-b border-gray-700">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
            Field Validation — {issues.length} issue{issues.length !== 1 ? "s" : ""}
          </span>
        </div>
        <div className="divide-y divide-gray-800">
          {sorted.map((r) => {
            const dotColor = r.priority === "critical"
              ? "bg-red-500" : r.priority === "important"
              ? "bg-orange-500" : "bg-yellow-500";
            const textColor = r.priority === "critical"
              ? "text-red-400" : r.priority === "important"
              ? "text-orange-400" : "text-yellow-400";
            return (
              <div key={r.field_name} className="flex items-start gap-2.5 px-3 py-2">
                <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${dotColor}`} />
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-gray-300">
                      {FIELD_LABELS[r.field_name] ?? r.field_name}
                    </span>
                    <span className={`text-[10px] font-semibold uppercase ${textColor}`}>
                      {r.priority}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">{r.message}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── Main panel ─────────────────────────────────────────────────────────────────
export function DetailPanel({ declaration, token, fieldDefs = [], onClose, onUpdate, onReview, onSubmit, onReprocess }) {
  const [imageData, setImageData]               = useState(null);
  const [imgW, setImgW]                         = useState(null);
  const [imgH, setImgH]                         = useState(null);
  const [validationResults, setValidationResults] = useState([]);
  const [imageFetched, setImageFetched]         = useState(false);
  const [ceisaOpen, setCeisaOpen]               = useState(false);
  const [reviewLoading, setReviewLoading]       = useState(false);
  const [note, setNote]                         = useState("");
  const [showOverlay, setShowOverlay]           = useState(true);
  const [showLightbox, setShowLightbox]         = useState(false);

  const id          = declaration.id;
  const riskBadge   = declaration.risk_badge ?? "yellow";
  const riskScore   = declaration.risk_score ?? 0;
  const confidence  = declaration.confidence_badge ?? "medium";
  const flagged     = declaration.flagged_fields ?? [];
  const fields      = declaration.extracted_fields ?? {};
  const reviewStatus = declaration.review_status ?? "pending";

  useEffect(() => {
    setImageData(null);
    setImgW(null);
    setImgH(null);
    setValidationResults([]);
    setImageFetched(false);
    setNote(declaration.review_note ?? "");
  }, [declaration.id]);

  useEffect(() => {
    if (imageFetched || !token) return;
    setImageFetched(true);
    fetch(`${API}/declarations/${id}/image`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data) return;
        if (data.image_data) setImageData(data.image_data);
        if (data.image_width) setImgW(data.image_width);
        if (data.image_height) setImgH(data.image_height);
        if (data.validation_results?.length) setValidationResults(data.validation_results);
      })
      .catch(() => {});
  }, [id, token, imageFetched]);

  const handleReview = async (status) => {
    setReviewLoading(true);
    try { await onReview(id, status, note); } finally { setReviewLoading(false); }
  };

  const riskBarColour = riskBadge === "green" ? "bg-emerald-500" : riskBadge === "red" ? "bg-red-500" : "bg-yellow-500";
  const riskTextColour = riskBadge === "green" ? "text-emerald-400" : riskBadge === "red" ? "text-red-400" : "text-yellow-400";

  const criticalIssues  = validationResults.filter((r) => !r.is_valid && r.priority === "critical").length;
  const importantIssues = validationResults.filter((r) => !r.is_valid && r.priority === "important").length;
  const hasBoxes        = validationResults.some((r) => r.bbox);

  return (
    <div className="fixed inset-0 z-30 flex">
      <div className="flex-1 bg-black/50" onClick={onClose} />

      <div className="w-[500px] bg-gray-900 border-l border-gray-800 flex flex-col h-full overflow-hidden shadow-2xl">
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
          {/* Document image with SVG overlay */}
          <div className="px-5 pt-4 pb-3">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Document</div>
              {hasBoxes && (
                <button
                  onClick={() => setShowOverlay((v) => !v)}
                  className="text-xs text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1"
                >
                  <span className={`w-2 h-2 rounded-full ${showOverlay ? "bg-blue-400" : "bg-gray-600"}`} />
                  {showOverlay ? "Hide overlay" : "Show overlay"}
                </button>
              )}
            </div>

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
              ) : showOverlay ? (
                <DocumentOverlay
                  imageData={imageData}
                  imgW={imgW}
                  imgH={imgH}
                  validationResults={validationResults}
                  onExpand={() => setShowLightbox(true)}
                />
              ) : (
                <div
                  className="relative group cursor-zoom-in"
                  onClick={() => setShowLightbox(true)}
                  title="Click to view full size"
                >
                  <img src={`data:${mime(imageData)};base64,${imageData}`} alt="Document"
                    className="w-full rounded-xl border border-gray-700 object-contain max-h-72" />
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 rounded-lg px-2 py-1 flex items-center gap-1 pointer-events-none">
                    <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
                    </svg>
                    <span className="text-white text-xs font-medium">Full size</span>
                  </div>
                </div>
              )
            ) : (
              <div className="flex items-center justify-center bg-gray-800 rounded-xl py-8 border border-gray-700">
                <span className="text-xs text-gray-600">{imageFetched ? "No image stored" : "Loading…"}</span>
              </div>
            )}

            {/* Overlay legend */}
            {hasBoxes && showOverlay && (
              <div className="mt-2 flex flex-wrap gap-3 text-[10px] text-gray-500">
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-red-500 inline-block" style={{borderTop:"2px solid #ef4444"}} /> Critical issue</span>
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 inline-block" style={{borderTop:"2px solid #f97316"}} /> Important issue</span>
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 inline-block" style={{borderTop:"2px dashed #eab308"}} /> Optional/missing</span>
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 inline-block" style={{borderTop:"2px solid #22c55e"}} /> Valid</span>
              </div>
            )}
          </div>

          {/* Validation issues summary */}
          <ValidationSummary validationResults={validationResults} />

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

          {/* Validation score pills */}
          {validationResults.length > 0 && (
            <div className="px-5 pb-4 flex gap-2">
              <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
                criticalIssues > 0
                  ? "bg-red-900/30 text-red-400 border-red-800"
                  : "bg-emerald-900/20 text-emerald-400 border-emerald-800/40"
              }`}>
                {criticalIssues > 0 ? `${criticalIssues} critical` : "✓ Critical OK"}
              </span>
              <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
                importantIssues > 0
                  ? "bg-orange-900/30 text-orange-400 border-orange-800"
                  : "bg-emerald-900/20 text-emerald-400 border-emerald-800/40"
              }`}>
                {importantIssues > 0 ? `${importantIssues} important` : "✓ Important OK"}
              </span>
            </div>
          )}

          {/* SHAP Explainer */}
          {declaration.shap_values?.length > 0 && (
            <div className="px-5 pb-4">
              <div className="bg-gray-800 rounded-xl p-4">
                <ShapExplainer shapValues={declaration.shap_values} riskBadge={riskBadge} riskScore={riskScore} />
              </div>
            </div>
          )}

          {/* Extraction method */}
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

          {/* Flagged issues */}
          {flagged.length > 0 && (
            <div className="px-5 pb-4">
              <div className="bg-red-900/20 border border-red-800/50 rounded-xl p-3 space-y-1">
                <div className="text-xs font-semibold text-red-400 mb-2">! Risk Flags</div>
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
              <FieldEditor
                fields={fields}
                validationResults={validationResults}
                fieldDefs={fieldDefs}
                onUpdate={(fieldName, value) => onUpdate(id, fieldName, value)}
              />
            </div>
          </div>

          {/* Review */}
          <div className="px-5 pb-6">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Manager Review</div>
            <div className="bg-gray-800 rounded-xl p-4 space-y-3">
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
                    <button onClick={() => handleReview("approved")} disabled={reviewLoading}
                      className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg text-sm font-semibold text-white transition-colors">
                      ✓ Approve
                    </button>
                    <button onClick={() => handleReview("rejected")} disabled={reviewLoading}
                      className="flex-1 py-2 bg-red-700 hover:bg-red-600 disabled:opacity-50 rounded-lg text-sm font-semibold text-white transition-colors">
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
                  <button onClick={() => handleReview("pending")}
                    className="text-xs text-gray-500 hover:text-gray-300 underline transition-colors">
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

      {showLightbox && imageData && !isPdf(imageData) && (
        <ImageLightbox
          imageData={imageData}
          imgW={imgW}
          imgH={imgH}
          validationResults={validationResults}
          showOverlay={showOverlay}
          onClose={() => setShowLightbox(false)}
        />
      )}
    </div>
  );
}

function ReviewStatusBadge({ status }) {
  const cfg = {
    pending:  "bg-yellow-900/40 text-yellow-400 border-yellow-700",
    approved: "bg-emerald-900/40 text-emerald-400 border-emerald-700",
    rejected: "bg-red-900/40 text-red-400 border-red-700",
  }[status] ?? "bg-gray-800 text-gray-400 border-gray-700";
  const label = { pending: "Pending", approved: "Approved", rejected: "Rejected" }[status] ?? status;
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${cfg}`}>{label}</span>
  );
}
