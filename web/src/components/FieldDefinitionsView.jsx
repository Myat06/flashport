import { useCallback, useState } from "react";
import { useAPI } from "../hooks/useAPI";
import { useFieldDefs } from "../hooks/useFieldDefs";

const PRIORITIES = ["critical", "important", "optional"];

const PRIORITY_COLORS = {
  critical:  "text-red-400 bg-red-900/30",
  important: "text-yellow-400 bg-yellow-900/30",
  optional:  "text-gray-400 bg-gray-700/40",
};

const DOC_TYPES = [
  { value: "commercial_invoice", label: "Commercial Invoice", short: "CI"  },
  { value: "bill_of_lading",     label: "Bill of Lading",     short: "BoL" },
  { value: "packing_list",       label: "Packing List",       short: "PL"  },
];

const DOC_TYPE_COLORS = {
  commercial_invoice: "bg-blue-900/40 text-blue-300 border-blue-700",
  bill_of_lading:     "bg-purple-900/40 text-purple-300 border-purple-700",
  packing_list:       "bg-teal-900/40 text-teal-300 border-teal-700",
};

function parseDocTypes(str) {
  if (!str) return [];
  return str.split(",").map(s => s.trim()).filter(Boolean);
}

function serializeDocTypes(arr) {
  if (!arr || arr.length === 0) return null;        // null → all doc types
  if (arr.length === DOC_TYPES.length) return null; // all checked = same as null
  return arr.join(",");
}

const EMPTY_FORM = {
  field_key: "", display_label: "", priority: "optional",
  extraction_keywords: "", risk_weight: 0, sort_order: 99,
  applicable_doc_types: [],  // empty = all doc types
  is_active: true,
};

export default function FieldDefinitionsView() {
  const { fieldDefs, loading, reload } = useFieldDefs();
  const api = useAPI();

  const [editing, setEditing]   = useState(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm]         = useState(EMPTY_FORM);
  const [saving, setSaving]     = useState(false);
  const [error, setError]       = useState("");

  const openCreate = () => { setForm(EMPTY_FORM); setError(""); setCreating(true); setEditing(null); };
  const openEdit   = (fd) => {
    setForm({
      display_label:        fd.display_label,
      priority:             fd.priority,
      extraction_keywords:  fd.extraction_keywords || "",
      risk_weight:          fd.risk_weight ?? 0,
      sort_order:           fd.sort_order ?? 99,
      applicable_doc_types: parseDocTypes(fd.applicable_doc_types),
      is_active:            fd.is_active,
    });
    setError("");
    setEditing(fd.id);
    setCreating(false);
  };
  const cancel = () => { setEditing(null); setCreating(false); setError(""); };

  const handleChange = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleDocTypeToggle = (val) => {
    setForm(f => {
      const current = f.applicable_doc_types;
      return {
        ...f,
        applicable_doc_types: current.includes(val)
          ? current.filter(t => t !== val)
          : [...current, val],
      };
    });
  };

  const save = useCallback(async () => {
    setSaving(true);
    setError("");
    try {
      const docTypesStr = serializeDocTypes(form.applicable_doc_types);
      if (creating) {
        const body = {
          ...form,
          risk_weight: Number(form.risk_weight),
          sort_order: Number(form.sort_order),
          applicable_doc_types: docTypesStr,
        };
        const res = await api.post("/field-definitions", body);
        if (!res.ok) { setError((await res.json()).detail || "Failed"); return; }
      } else {
        const body = {
          display_label:        form.display_label,
          priority:             form.priority,
          extraction_keywords:  form.extraction_keywords,
          risk_weight:          Number(form.risk_weight),
          sort_order:           Number(form.sort_order),
          applicable_doc_types: docTypesStr,
          is_active:            form.is_active,
        };
        const res = await api.patch(`/field-definitions/${editing}`, body);
        if (!res.ok) { setError((await res.json()).detail || "Failed"); return; }
      }
      cancel();
      reload();
    } catch (e) {
      setError(e.message || "Network error");
    } finally {
      setSaving(false);
    }
  }, [creating, editing, form, api, reload]);

  const remove = useCallback(async (id) => {
    if (!confirm("Delete this field definition?")) return;
    await api.del(`/field-definitions/${id}`);
    reload();
  }, [api, reload]);

  const toggle = useCallback(async (fd) => {
    await api.patch(`/field-definitions/${fd.id}`, { is_active: !fd.is_active });
    reload();
  }, [api, reload]);

  // Group field defs by their applicable doc types for display
  const grouped = {
    all:                fieldDefs.filter(fd => !fd.applicable_doc_types),
    commercial_invoice: fieldDefs.filter(fd => fd.applicable_doc_types?.includes("commercial_invoice") && !fd.applicable_doc_types?.includes("bill_of_lading") && !fd.applicable_doc_types?.includes("packing_list")),
    bill_of_lading:     fieldDefs.filter(fd => fd.applicable_doc_types?.includes("bill_of_lading") && !fd.applicable_doc_types?.includes("commercial_invoice")),
    packing_list:       fieldDefs.filter(fd => fd.applicable_doc_types?.includes("packing_list") && !fd.applicable_doc_types?.includes("commercial_invoice") && !fd.applicable_doc_types?.includes("bill_of_lading")),
    multi:              fieldDefs.filter(fd => {
      if (!fd.applicable_doc_types) return false;
      const parts = fd.applicable_doc_types.split(",");
      return parts.length > 1;
    }),
  };

  const sections = [
    { key: "all",                title: "All Document Types",   color: "border-gray-600",   heading: "text-gray-300"  },
    { key: "commercial_invoice", title: "Commercial Invoice",   color: "border-blue-700",   heading: "text-blue-300"  },
    { key: "bill_of_lading",     title: "Bill of Lading",       color: "border-purple-700", heading: "text-purple-300"},
    { key: "packing_list",       title: "Packing List",         color: "border-teal-700",   heading: "text-teal-300"  },
    { key: "multi",              title: "Multiple Doc Types",   color: "border-orange-700", heading: "text-orange-300"},
  ];

  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-white">Field Schema</h2>
          <p className="text-sm text-gray-400 mt-0.5">
            Define what fields to extract per document type. Only relevant fields are extracted, validated, and scored for each scan.
          </p>
        </div>
        <button
          onClick={openCreate}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium text-white"
        >
          + Add Field
        </button>
      </div>

      {creating && (
        <FormPanel
          title="New Field"
          form={form} onChange={handleChange} onDocTypeToggle={handleDocTypeToggle}
          onSave={save} onCancel={cancel} saving={saving} error={error} isCreate
        />
      )}

      {loading ? (
        <p className="text-gray-500 text-sm">Loading…</p>
      ) : (
        <div className="space-y-6">
          {sections.map(({ key, title, color, heading }) => {
            const items = grouped[key];
            if (!items?.length) return null;
            return (
              <div key={key}>
                <div className={`flex items-center gap-2 mb-2 pb-1 border-b ${color}`}>
                  <span className={`text-xs font-bold uppercase tracking-wider ${heading}`}>{title}</span>
                  <span className="text-gray-600 text-xs">{items.length} field{items.length !== 1 ? "s" : ""}</span>
                </div>
                <div className="space-y-1.5">
                  {items.map(fd => (
                    <FieldRow
                      key={fd.id}
                      fd={fd}
                      isEditing={editing === fd.id}
                      form={form}
                      onChange={handleChange}
                      onDocTypeToggle={handleDocTypeToggle}
                      onEdit={() => openEdit(fd)}
                      onSave={save}
                      onCancel={cancel}
                      onToggle={() => toggle(fd)}
                      onRemove={() => remove(fd.id)}
                      saving={saving}
                      error={error}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function FieldRow({ fd, isEditing, form, onChange, onDocTypeToggle, onEdit, onSave, onCancel, onToggle, onRemove, saving, error }) {
  const docTypes = parseDocTypes(fd.applicable_doc_types);

  if (isEditing) {
    return (
      <div className="bg-gray-900 rounded-xl border border-blue-700 p-4">
        <FormPanel
          title={`Edit: ${fd.field_key}`}
          form={form} onChange={onChange} onDocTypeToggle={onDocTypeToggle}
          onSave={onSave} onCancel={onCancel} saving={saving} error={error}
        />
      </div>
    );
  }

  return (
    <div className="flex items-start gap-4 bg-gray-800 rounded-xl border border-gray-700 px-4 py-3">
      <span className="text-gray-600 text-xs mt-1 w-6 text-center shrink-0">{fd.sort_order}</span>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-blue-300 text-sm">{fd.field_key}</span>
          <span className="text-gray-500 text-xs">·</span>
          <span className="text-white text-sm">{fd.display_label}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${PRIORITY_COLORS[fd.priority]}`}>
            {fd.priority}
          </span>
          {/* Doc type badges */}
          {docTypes.length > 0
            ? docTypes.map(dt => {
                const cfg = DOC_TYPES.find(d => d.value === dt);
                return (
                  <span key={dt} className={`text-xs px-1.5 py-0.5 rounded border font-mono ${DOC_TYPE_COLORS[dt] ?? "text-gray-400 bg-gray-700 border-gray-600"}`}>
                    {cfg?.short ?? dt}
                  </span>
                );
              })
            : <span className="text-xs text-gray-500 italic">all types</span>
          }
          {fd.is_builtin && <span className="text-xs px-2 py-0.5 rounded-full text-gray-500 bg-gray-700/50">built-in</span>}
          {!fd.is_active && <span className="text-xs px-2 py-0.5 rounded-full text-orange-400 bg-orange-900/30">disabled</span>}
        </div>
        <p className="text-gray-500 text-xs mt-1 truncate">
          <span className="text-gray-600">Keywords: </span>{fd.extraction_keywords || "—"}
        </p>
        <p className="text-gray-500 text-xs">
          <span className="text-gray-600">Risk weight: </span>
          <span className={fd.risk_weight > 0 ? "text-orange-400" : "text-gray-600"}>
            {fd.risk_weight > 0 ? `+${fd.risk_weight} pts when missing` : "0"}
          </span>
        </p>
      </div>

      <div className="flex items-center gap-1 shrink-0">
        <button onClick={onToggle} className="px-2 py-1 text-xs rounded text-gray-400 hover:text-white hover:bg-gray-700">
          {fd.is_active ? "Disable" : "Enable"}
        </button>
        <button onClick={onEdit} className="px-2 py-1 text-xs rounded text-blue-400 hover:text-white hover:bg-blue-900/40">
          Edit
        </button>
        {!fd.is_builtin && (
          <button onClick={onRemove} className="px-2 py-1 text-xs rounded text-red-400 hover:text-white hover:bg-red-900/40">
            Delete
          </button>
        )}
      </div>
    </div>
  );
}

function FormPanel({ title, form, onChange, onDocTypeToggle, onSave, onCancel, saving, error, isCreate }) {
  const allChecked = form.applicable_doc_types.length === 0 || form.applicable_doc_types.length === DOC_TYPES.length;

  return (
    <div className="bg-gray-900 rounded-xl border border-blue-800 p-4 mb-2">
      <h3 className="text-sm font-semibold text-white mb-3">{title}</h3>

      <div className="grid grid-cols-2 gap-3 mb-3">
        {isCreate && (
          <div>
            <label className="block text-xs text-gray-400 mb-1">Field Key <span className="text-red-400">*</span></label>
            <input
              className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm text-white font-mono"
              placeholder="e.g. payment_terms"
              value={form.field_key}
              onChange={e => onChange("field_key", e.target.value.toLowerCase().replace(/\s+/g, "_"))}
            />
          </div>
        )}
        <div>
          <label className="block text-xs text-gray-400 mb-1">Display Label <span className="text-red-400">*</span></label>
          <input
            className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm text-white"
            placeholder="e.g. Payment Terms"
            value={form.display_label}
            onChange={e => onChange("display_label", e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Priority</label>
          <select
            className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm text-white"
            value={form.priority}
            onChange={e => onChange("priority", e.target.value)}
          >
            {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Risk Weight (pts when missing)</label>
          <input
            type="number" min="0" max="50"
            className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm text-white"
            value={form.risk_weight}
            onChange={e => onChange("risk_weight", e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Sort Order</label>
          <input
            type="number" min="1" max="999"
            className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm text-white"
            value={form.sort_order}
            onChange={e => onChange("sort_order", e.target.value)}
          />
        </div>
        {!isCreate && (
          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" className="w-4 h-4 accent-blue-500"
                checked={form.is_active} onChange={e => onChange("is_active", e.target.checked)} />
              <span className="text-sm text-gray-300">Active</span>
            </label>
          </div>
        )}
      </div>

      {/* Document type applicability */}
      <div className="mb-3">
        <label className="block text-xs text-gray-400 mb-2">
          Applies to document types
          <span className="text-gray-600 ml-1">(leave all unchecked = every type)</span>
        </label>
        <div className="flex gap-3 flex-wrap">
          {DOC_TYPES.map(({ value, label }) => {
            const checked = form.applicable_doc_types.includes(value);
            return (
              <label key={value} className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  className="w-4 h-4 accent-blue-500"
                  checked={checked}
                  onChange={() => onDocTypeToggle(value)}
                />
                <span className={`text-sm transition-colors ${checked ? "text-white" : "text-gray-500 group-hover:text-gray-300"}`}>
                  {label}
                </span>
              </label>
            );
          })}
        </div>
        {allChecked && (
          <p className="text-gray-600 text-xs mt-1">This field will be extracted and validated for every document type.</p>
        )}
      </div>

      <div className="mb-3">
        <label className="block text-xs text-gray-400 mb-1">
          Extraction Keywords <span className="text-gray-500">(comma-separated synonyms the system looks for in OCR text)</span>
        </label>
        <textarea
          rows={2}
          className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm text-white resize-none"
          placeholder="e.g. Payment Terms, Syarat Pembayaran, Terms of Payment, Conditions"
          value={form.extraction_keywords}
          onChange={e => onChange("extraction_keywords", e.target.value)}
        />
      </div>

      {error && <p className="text-red-400 text-xs mb-2">{error}</p>}

      <div className="flex gap-2">
        <button onClick={onSave} disabled={saving}
          className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded text-sm text-white font-medium">
          {saving ? "Saving…" : "Save"}
        </button>
        <button onClick={onCancel}
          className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-300">
          Cancel
        </button>
      </div>
    </div>
  );
}
