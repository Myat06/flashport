import { useEffect, useState } from "react";
import { useAPI } from "../hooks/useAPI";

const FIELDS = ["hs_code", "importer", "exporter", "invoice_value", "container_id", "net_weight", "vessel_name", "port_of_origin"];
const CONDITIONS = [
  { value: "missing", label: "Is Missing" },
  { value: "starts_with", label: "Starts With" },
  { value: "equals", label: "Equals" },
  { value: "contains", label: "Contains" },
  { value: "gt", label: "Greater Than (numeric)" },
];

export function RiskRulesView({ token }) {
  const api = useAPI(token);
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: "", field: "hs_code", condition: "starts_with", value: "", risk_boost: 10, flag_label: "" });

  const load = () => api.get("/risk-rules").then((data) => { setRules(data); setLoading(false); });
  useEffect(() => { load(); }, []); // eslint-disable-line

  const handleAdd = async (e) => {
    e.preventDefault();
    await api.post("/risk-rules", form);
    setForm({ name: "", field: "hs_code", condition: "starts_with", value: "", risk_boost: 10, flag_label: "" });
    setShowAdd(false);
    load();
  };

  const toggleRule = async (rule) => {
    await api.patch(`/risk-rules/${rule.id}`, { is_active: !rule.is_active });
    load();
  };

  const deleteRule = async (id) => {
    await api.del(`/risk-rules/${id}`);
    load();
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Risk Rules</h2>
          <p className="text-xs text-gray-500 mt-0.5">Configure custom scoring rules — applied on every scan</p>
        </div>
        <button onClick={() => setShowAdd((v) => !v)} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-semibold transition-colors">
          + Add Rule
        </button>
      </div>

      {showAdd && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-4">New Rule</h3>
          <form onSubmit={handleAdd} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Rule Name</label>
                <input required value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. Restricted HS Prefix"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Risk Boost (points)</label>
                <input type="number" min={1} max={100} value={form.risk_boost}
                  onChange={(e) => setForm((f) => ({ ...f, risk_boost: parseInt(e.target.value) }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Field</label>
                <select value={form.field} onChange={(e) => setForm((f) => ({ ...f, field: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                  {FIELDS.map((f) => <option key={f} value={f}>{f.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Condition</label>
                <select value={form.condition} onChange={(e) => setForm((f) => ({ ...f, condition: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                  {CONDITIONS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Value {form.condition === "missing" && "(not needed)"}</label>
                <input value={form.value} onChange={(e) => setForm((f) => ({ ...f, value: e.target.value }))}
                  disabled={form.condition === "missing"}
                  placeholder={form.condition === "missing" ? "—" : "e.g. 9301"}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 disabled:opacity-40" />
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => setShowAdd(false)} className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition-colors">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-semibold transition-colors">Create Rule</button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-[2fr_1fr_1fr_80px_80px_80px_60px] gap-4 px-5 py-3 border-b border-gray-800 text-xs font-semibold text-gray-500 uppercase tracking-wide">
          <span>Rule</span><span>Field</span><span>Condition</span><span>Value</span><span>Boost</span><span>Status</span><span />
        </div>
        {loading ? (
          <div className="px-5 py-8 text-center text-gray-600 text-sm">Loading…</div>
        ) : rules.length === 0 ? (
          <div className="px-5 py-8 text-center text-gray-600 text-sm">No custom rules — baseline scoring only.</div>
        ) : (
          <div className="divide-y divide-gray-800/60">
            {rules.map((r) => (
              <div key={r.id} className={`grid grid-cols-[2fr_1fr_1fr_80px_80px_80px_60px] gap-4 px-5 py-3.5 items-center ${!r.is_active ? "opacity-50" : ""}`}>
                <span className="text-sm font-medium">{r.name}</span>
                <span className="text-xs text-blue-400 font-mono">{r.field}</span>
                <span className="text-xs text-gray-400">{CONDITIONS.find((c) => c.value === r.condition)?.label ?? r.condition}</span>
                <span className="text-xs font-mono text-gray-300">{r.value || "—"}</span>
                <span className="text-xs font-bold text-orange-400">+{r.risk_boost}</span>
                <button onClick={() => toggleRule(r)}
                  className={`text-xs px-2 py-1 rounded-full border transition-colors ${r.is_active ? "text-emerald-400 border-emerald-800 bg-emerald-900/20 hover:bg-emerald-900/40" : "text-gray-500 border-gray-700 bg-gray-800 hover:bg-gray-700"}`}>
                  {r.is_active ? "Active" : "Off"}
                </button>
                <button onClick={() => deleteRule(r.id)} className="text-gray-600 hover:text-red-400 transition-colors text-xs">Delete</button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
