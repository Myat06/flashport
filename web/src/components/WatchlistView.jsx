import { useEffect, useState } from "react";
import { useAPI } from "../hooks/useAPI";

const TYPE_LABELS = { importer: "Importer", exporter: "Exporter", hs_code: "HS Code" };

export function WatchlistView({ token }) {
  const api = useAPI(token);
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ entity_type: "importer", value: "", reason: "" });
  const [error, setError] = useState("");

  const load = () => {
    api.get("/watchlist").then((data) => { setEntries(data); setLoading(false); });
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  const handleAdd = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/watchlist", form);
      setForm((f) => ({ ...f, value: "", reason: "" }));
      load();
    } catch {
      setError("Entry already on watchlist or failed to add");
    }
  };

  const handleRemove = async (id) => {
    await api.del(`/watchlist/${id}`);
    load();
  };

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold">Watchlist</h2>
        <p className="text-xs text-gray-500 mt-0.5">Flag importers, exporters, or HS codes for automatic risk elevation</p>
      </div>

      {/* Add form */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-4">Add Entry</h3>
        <form onSubmit={handleAdd} className="flex gap-3 flex-wrap">
          <select
            value={form.entity_type}
            onChange={(e) => setForm((f) => ({ ...f, entity_type: e.target.value }))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          >
            <option value="importer">Importer</option>
            <option value="exporter">Exporter</option>
            <option value="hs_code">HS Code</option>
          </select>
          <input
            required value={form.value}
            onChange={(e) => setForm((f) => ({ ...f, value: e.target.value }))}
            placeholder="Company name or HS code"
            className="flex-1 min-w-48 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          />
          <input
            value={form.reason}
            onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))}
            placeholder="Reason (optional)"
            className="flex-1 min-w-48 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          />
          <button type="submit" className="px-4 py-2 bg-red-700 hover:bg-red-600 rounded-lg text-sm font-semibold transition-colors">
            + Add to Watchlist
          </button>
        </form>
        {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
      </div>

      {/* Entries table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-[100px_1fr_2fr_120px] gap-4 px-5 py-3 border-b border-gray-800 text-xs font-semibold text-gray-500 uppercase tracking-wide">
          <span>Type</span><span>Value</span><span>Reason</span><span>Action</span>
        </div>
        {loading ? (
          <div className="px-5 py-8 text-center text-gray-600 text-sm">Loading…</div>
        ) : entries.length === 0 ? (
          <div className="px-5 py-8 text-center text-gray-600 text-sm">No watchlist entries — add entities above.</div>
        ) : (
          <div className="divide-y divide-gray-800/60">
            {entries.map((e) => (
              <div key={e.id} className="grid grid-cols-[100px_1fr_2fr_120px] gap-4 px-5 py-3.5 items-center">
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full border border-red-800 text-red-400 bg-red-900/20 w-fit">
                  {TYPE_LABELS[e.entity_type] ?? e.entity_type}
                </span>
                <span className="text-sm font-medium">{e.value}</span>
                <span className="text-sm text-gray-400">{e.reason || <span className="text-gray-600 italic">No reason given</span>}</span>
                <button
                  onClick={() => handleRemove(e.id)}
                  className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-red-900/40 hover:text-red-400 text-gray-400 rounded-lg transition-colors"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
