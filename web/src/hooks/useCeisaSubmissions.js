import { useCallback, useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function useCeisaSubmissions(token) {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(() => {
    if (!token) return;
    fetch(`${API}/ceisa/submissions`, {
      headers: { "Authorization": `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => { setSubmissions(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [token]);

  useEffect(() => { refresh(); }, [refresh]);

  return { submissions, loading, refresh };
}
