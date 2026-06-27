import { useEffect, useState } from "react";
import { useAPI } from "../hooks/useAPI";

const PRIORITY_CFG = {
  critical:  { label: "Critical",  bg: "bg-red-900/30",    text: "text-red-400",    border: "border-red-800"    },
  important: { label: "Important", bg: "bg-orange-900/30", text: "text-orange-400", border: "border-orange-800" },
  optional:  { label: "Optional",  bg: "bg-yellow-900/20", text: "text-yellow-400", border: "border-yellow-800" },
};

export function FieldValidationRulesView({ token, fieldDefs = [] }) {
  const api = useAPI(token);
  const fieldOptions = fieldDefs.filter(fd => fd.is_active).map(fd => fd.field_key);
  const fieldLabels  = Object.fromEntries(fieldDefs.map(fd => [fd.field_key, fd.display_label]));
  const firstKey     = fieldOptions[0] ?? "hs_code";
  const BLANK = {
    name: "", field_name: firstKey, rule_type: "regex",
    priority: "important", min_val: "", max_val: "",
    pattern: "", allowed_values: "", max_length: "", error_message: "",
  };
  const [rules, setRules]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm]       = useState(null);   // null = closed
  const [saving, setSaving]   = useState(false);

  const load = async () => {
    setLoading(true);
    try { setRules(await api.get("/field-validation-rules")); } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const openNew  = () => setForm({ ...BLANK, _isNew: true });
  const openEdit = (r) => setForm({ ...r, _isNew: false });
  const closeForm = () => setForm(null);

  const save = async () => {
    if (!form.name || !form.field_name || !form.rule_type) return;
    setSaving(true);
    try {
      const body = { ...form };
      delete body._isNew;
      if (form._isNew) {
        await api.post("/field-validation-rules", body);
      } else {
        await api.patch(`/field-validation-rules/${form.id}`, body);
      }
      await load();
      closeForm();
    } finally {
      setSaving(false);
    }
  };

  const toggle = async (rule) => {
    await api.patch(`/field-validation-rules/${rule.id}`, { is_active: !rule.is_active });
    await load();
  };

  const remove = async (rule) => {
    if (rule.is_builtin) return;
    if (!confirm(`Delete rule "${rule.name}"?`)) return;
    await api.del(`/field-validation-rules/${rule.id}`);
    await load();
  };

  // Group rules by field_name; include any rules for fields not in current fieldDefs
  const allFieldKeys = [...new Set([...fieldOptions, ...rules.map(r => r.field_name)])];
  const grouped = allFieldKeys.reduce((acc, f) => {
    acc[f] = rules.filter((r) => r.field_name === f);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-500 mt-0.5">
            Define format, range, and required rules per field. Violations highlight in red on the document image
            and add to risk score.
          </p>
        </div>
        <button
          onClick={openNew}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-xs font-semibold transition-colors"
        >
          + Add Rule
        </button>
      </div>

      {loading ? (
        <div className="text-xs text-gray-500">Loading…</div>
      ) : (
        <div className="space-y-4">
          {allFieldKeys.map((fieldName) => {
            const fieldRules = grouped[fieldName];
            if (!fieldRules.length) return null;
            return (
              <div key={fieldName} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-800 bg-gray-800/40">
                  <span className="text-sm font-semibold text-gray-200">{fieldLabels[fieldName] ?? fieldName}</span>
                </div>
                <div className="divide-y divide-gray-800">
                  {fieldRules.map((rule) => {
                    const pcfg = PRIORITY_CFG[rule.priority] ?? PRIORITY_CFG.optional;
                    return (
                      <div key={rule.id} className="flex items-center gap-3 px-4 py-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm font-medium text-gray-200">{rule.name}</span>
                            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${pcfg.bg} ${pcfg.text} ${pcfg.border}`}>
                              {pcfg.label}
                            </span>
                            <span className="text-[10px] text-gray-500 font-mono bg-gray-800 px-1.5 py-0.5 rounded">
                              {rule.rule_type}
                            </span>
                            {rule.is_builtin && (
                              <span className="text-[10px] text-blue-400">built-in</span>
                            )}
                          </div>
                          {rule.error_message && (
                            <p className="text-xs text-gray-500 mt-0.5 truncate">{rule.error_message}</p>
                          )}
                        </div>

                        {/* Toggle */}
                        <button
                          onClick={() => toggle(rule)}
                          className={`relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors ${
                            rule.is_active ? "bg-blue-600" : "bg-gray-700"
                          }`}
                        >
                          <span className={`inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform mt-0.5 ${
                            rule.is_active ? "translate-x-4" : "translate-x-0.5"
                          }`} />
                        </button>

                        {/* Edit */}
                        <button
                          onClick={() => openEdit(rule)}
                          className="text-gray-500 hover:text-gray-300 transition-colors p-1"
                          title="Edit"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Z" />
                          </svg>
                        </button>

                        {/* Delete (non-builtin only) */}
                        {!rule.is_builtin && (
                          <button
                            onClick={() => remove(rule)}
                            className="text-gray-600 hover:text-red-400 transition-colors p-1"
                            title="Delete"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916" />
                            </svg>
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {!rules.length && (
            <div className="text-center py-12 text-gray-600">
              <p className="text-sm">No validation rules yet.</p>
              <p className="text-xs mt-1">Click "Add Rule" to create your first rule.</p>
            </div>
          )}
        </div>
      )}

      {/* Add / Edit modal */}
      {form && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <h3 className="text-base font-semibold mb-4">{form._isNew ? "New Validation Rule" : "Edit Rule"}</h3>

            <div className="space-y-3">
              <Field label="Rule Name">
                <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. HS Code format check"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </Field>

              <div className="grid grid-cols-2 gap-3">
                <Field label="Field">
                  <select value={form.field_name} onChange={(e) => setForm((f) => ({ ...f, field_name: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                    {allFieldKeys.map((f) => <option key={f} value={f}>{fieldLabels[f] ?? f}</option>)}
                  </select>
                </Field>
                <Field label="Priority">
                  <select value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                    <option value="critical">Critical</option>
                    <option value="important">Important</option>
                    <option value="optional">Optional</option>
                  </select>
                </Field>
              </div>

              <Field label="Rule Type">
                <select value={form.rule_type} onChange={(e) => setForm((f) => ({ ...f, rule_type: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                  <option value="required">Required (must not be empty)</option>
                  <option value="regex">Regex pattern</option>
                  <option value="range">Numeric range</option>
                  <option value="enum">Allowed values (enum)</option>
                  <option value="max_length">Max length</option>
                </select>
              </Field>

              {form.rule_type === "regex" && (
                <Field label="Pattern (regex)">
                  <input value={form.pattern} onChange={(e) => setForm((f) => ({ ...f, pattern: e.target.value }))}
                    placeholder={`e.g. ^\\d{4}\\.\\d{2}\\.\\d{2,4}$`}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-500" />
                </Field>
              )}

              {form.rule_type === "range" && (
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Min value">
                    <input type="number" value={form.min_val} onChange={(e) => setForm((f) => ({ ...f, min_val: e.target.value }))}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
                  </Field>
                  <Field label="Max value">
                    <input type="number" value={form.max_val} onChange={(e) => setForm((f) => ({ ...f, max_val: e.target.value }))}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
                  </Field>
                </div>
              )}

              {form.rule_type === "enum" && (
                <Field label="Allowed values (comma-separated)">
                  <input value={form.allowed_values} onChange={(e) => setForm((f) => ({ ...f, allowed_values: e.target.value }))}
                    placeholder="USD,EUR,SGD,IDR"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
                </Field>
              )}

              {form.rule_type === "max_length" && (
                <Field label="Max length (chars)">
                  <input type="number" value={form.max_length} onChange={(e) => setForm((f) => ({ ...f, max_length: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
                </Field>
              )}

              <Field label="Error message (shown to manager)">
                <input value={form.error_message} onChange={(e) => setForm((f) => ({ ...f, error_message: e.target.value }))}
                  placeholder="e.g. HS code must be 8-digit format"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </Field>
            </div>

            <div className="flex gap-2 mt-5">
              <button onClick={closeForm}
                className="flex-1 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-medium transition-colors">
                Cancel
              </button>
              <button onClick={save} disabled={saving || !form.name}
                className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-semibold transition-colors">
                {saving ? "Saving…" : "Save Rule"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-xs text-gray-400 mb-1">{label}</label>
      {children}
    </div>
  );
}
