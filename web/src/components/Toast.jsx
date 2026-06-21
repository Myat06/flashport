export function Toast({ message, type, onClose }) {
  const colours = {
    success: "bg-emerald-900 border-emerald-700 text-emerald-200",
    error: "bg-red-900 border-red-700 text-red-200",
    warning: "bg-yellow-900 border-yellow-700 text-yellow-200",
  };
  const icons = { success: "✅", error: "🔴", warning: "⚠️" };

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in">
      <div className={`flex items-start gap-3 px-4 py-3 rounded-lg border shadow-xl max-w-sm ${colours[type]}`}>
        <span className="text-lg mt-0.5">{icons[type]}</span>
        <span className="text-sm font-medium flex-1">{message}</span>
        <button onClick={onClose} className="text-current opacity-60 hover:opacity-100 ml-2 text-lg leading-none">×</button>
      </div>
    </div>
  );
}
