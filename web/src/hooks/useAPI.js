const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function useAPI(token) {
  const headers = (extra = {}) => ({
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
    ...extra,
  });

  const get = (path) =>
    fetch(`${API}${path}`, { headers: headers() }).then((r) => r.json());

  const post = (path, body) =>
    fetch(`${API}${path}`, { method: "POST", headers: headers(), body: JSON.stringify(body) }).then((r) => r.json());

  const patch = (path, body) =>
    fetch(`${API}${path}`, { method: "PATCH", headers: headers(), body: JSON.stringify(body) }).then((r) => r.json());

  const del = (path) =>
    fetch(`${API}${path}`, { method: "DELETE", headers: headers() }).then((r) => r.json());

  const download = (path, filename) =>
    fetch(`${API}${path}`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
      });

  return { get, post, patch, del, download };
}
