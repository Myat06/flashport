import { useEffect, useState } from "react";
import { useAPI } from "../hooks/useAPI";

export function OperatorsView({ token }) {
  const api = useAPI(token);
  const [operators, setOperators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ employee_id: "", name: "", pin: "" });
  const [resetPin, setResetPin] = useState({});
  const [error, setError] = useState("");

  const load = () => {
    api.get("/operators").then((data) => { setOperators(data); setLoading(false); });
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  const handleAdd = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/operators", form);
      setForm({ employee_id: "", name: "", pin: "" });
      setShowAdd(false);
      load();
    } catch {
      setError("Failed to add operator");
    }
  };

  const toggleActive = async (op) => {
    await api.patch(`/operators/${op.employee_id}`, { is_active: !op.is_active });
    load();
  };

  const handleResetPin = async (employeeId) => {
    const pin = resetPin[employeeId];
    if (!pin) return;
    await api.post(`/operators/${employeeId}/reset-pin`, { new_pin: pin });
    setResetPin((p) => ({ ...p, [employeeId]: "" }));
    alert("PIN reset successfully");
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Field Operators</h2>
          <p className="text-xs text-gray-500 mt-0.5">{operators.length} operator{operators.length !== 1 ? "s" : ""} registered</p>
        </div>
        <button
          onClick={() => setShowAdd((v) => !v)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-semibold transition-colors"
        >
          + Add Operator
        </button>
      </div>

      {showAdd && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-4">New Operator</h3>
          <form onSubmit={handleAdd} className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Employee ID</label>
              <input
                required value={form.employee_id}
                onChange={(e) => setForm((f) => ({ ...f, employee_id: e.target.value }))}
                placeholder="CDP-004"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Full Name</label>
              <input
                required value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Ahmad Fauzi"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Initial PIN</label>
              <input
                required type="password" value={form.pin}
                onChange={(e) => setForm((f) => ({ ...f, pin: e.target.value }))}
                placeholder="••••"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            {error && <p className="col-span-3 text-xs text-red-400">{error}</p>}
            <div className="col-span-3 flex gap-2 justify-end">
              <button type="button" onClick={() => setShowAdd(false)}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition-colors">Cancel</button>
              <button type="submit"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-semibold transition-colors">Create</button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-[1fr_1.5fr_100px_200px_80px] gap-4 px-5 py-3 border-b border-gray-800 text-xs font-semibold text-gray-500 uppercase tracking-wide">
          <span>Employee ID</span><span>Name</span><span>Status</span><span>Reset PIN</span><span>Action</span>
        </div>
        {loading ? (
          <div className="px-5 py-8 text-center text-gray-600 text-sm">Loading…</div>
        ) : operators.length === 0 ? (
          <div className="px-5 py-8 text-center text-gray-600 text-sm">No operators yet.</div>
        ) : (
          <div className="divide-y divide-gray-800/60">
            {operators.map((op) => (
              <div key={op.employee_id} className="grid grid-cols-[1fr_1.5fr_100px_200px_80px] gap-4 px-5 py-3.5 items-center">
                <span className="font-mono text-sm text-blue-400">{op.employee_id}</span>
                <span className="text-sm">{op.name}</span>
                <span>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${op.is_active ? "text-emerald-400 bg-emerald-900/20 border-emerald-800" : "text-gray-500 bg-gray-800 border-gray-700"}`}>
                    {op.is_active ? "Active" : "Inactive"}
                  </span>
                </span>
                <div className="flex gap-1">
                  <input
                    type="password"
                    placeholder="New PIN"
                    value={resetPin[op.employee_id] || ""}
                    onChange={(e) => setResetPin((p) => ({ ...p, [op.employee_id]: e.target.value }))}
                    className="w-24 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs focus:outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={() => handleResetPin(op.employee_id)}
                    disabled={!resetPin[op.employee_id]}
                    className="px-2 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 rounded text-xs transition-colors"
                  >Reset</button>
                </div>
                <button
                  onClick={() => toggleActive(op)}
                  className={`text-xs px-2 py-1 rounded transition-colors ${op.is_active ? "bg-red-900/30 text-red-400 hover:bg-red-900/50" : "bg-emerald-900/30 text-emerald-400 hover:bg-emerald-900/50"}`}
                >
                  {op.is_active ? "Deactivate" : "Activate"}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
