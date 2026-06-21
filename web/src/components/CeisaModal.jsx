import { useState } from "react";

const JALUR_CONFIG = {
  hijau: { label: "Jalur Hijau", colour: "text-emerald-400", bg: "bg-emerald-900/30 border-emerald-700", icon: "✅" },
  kuning: { label: "Jalur Kuning", colour: "text-yellow-400", bg: "bg-yellow-900/30 border-yellow-700", icon: "⚠️" },
  merah: { label: "Jalur Merah", colour: "text-red-400", bg: "bg-red-900/30 border-red-700", icon: "🔴" },
};

export function CeisaModal({ declarationId, onClose, onSubmit }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const res = await onSubmit(declarationId);
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  const cfg = result ? JALUR_CONFIG[result.jalur] : null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-md p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-semibold">Submit to CEISA</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl leading-none">×</button>
        </div>

        {!result ? (
          <>
            <p className="text-sm text-gray-400">
              Declaration will be submitted to the CEISA gateway. A Jalur (channel) response will be returned immediately.
            </p>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg font-semibold transition-colors"
            >
              {loading ? "Submitting…" : "Submit Declaration"}
            </button>
          </>
        ) : (
          <div className={`rounded-lg border p-4 space-y-2 ${cfg.bg}`}>
            <div className="text-2xl">{cfg.icon}</div>
            <div className={`text-xl font-bold ${cfg.colour}`}>{cfg.label}</div>
            <div className="text-sm text-gray-300">{result.response_message}</div>
            <div className="text-xs text-gray-500 pt-1">
              Code: {result.response_code}
            </div>
            <button
              onClick={onClose}
              className="mt-2 w-full py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
