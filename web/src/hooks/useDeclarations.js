import { useEffect, useRef, useState } from "react";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const WS = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";

function authHeaders(token) {
  return { "Authorization": `Bearer ${token}` };
}

export function useDeclarations(token) {
  const [declarations, setDeclarations] = useState([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const wsRef = useRef(null);

  const refetch = () => {
    if (!token) return;
    fetch(`${API}/declarations`, { headers: authHeaders(token) })
      .then((r) => r.json())
      .then((data) => { setDeclarations(data); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { refetch(); }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(`${WS}/ws`);
      wsRef.current = ws;
      ws.onopen = () => {
        setConnected(true);
        // Re-fetch full list — records may have synced while the socket was down
        if (token) {
          fetch(`${API}/declarations`, { headers: authHeaders(token) })
            .then((r) => r.json())
            .then(setDeclarations)
            .catch(() => {});
        }
      };
      ws.onclose = () => { setConnected(false); setTimeout(connect, 3000); };
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.event === "new_declaration") {
          setDeclarations((prev) => {
            // Avoid duplicate if refetch already added this record
            const exists = prev.some((d) => (d.declaration_id ?? d.id) === (msg.data.declaration_id ?? msg.data.id));
            return exists ? prev : [msg.data, ...prev];
          });
        }
      };
    };
    connect();
    return () => wsRef.current?.close();
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const updateField = async (declarationId, fieldName, fieldValue) => {
    await fetch(`${API}/declarations/${declarationId}/field`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders(token) },
      body: JSON.stringify({ field_name: fieldName, field_value: fieldValue, reviewed_by: "manager" }),
    });
    setDeclarations((prev) =>
      prev.map((d) => {
        if (d.declaration_id !== declarationId && d.id !== declarationId) return d;
        return { ...d, extracted_fields: { ...d.extracted_fields, [fieldName]: fieldValue } };
      })
    );
  };

  const submitToCeisa = async (declarationId) => {
    const res = await fetch(`${API}/ceisa/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders(token) },
      body: JSON.stringify({ declaration_id: declarationId, submitted_by: "manager" }),
    });
    return res.json();
  };

  return { declarations, connected, loading, updateField, submitToCeisa, refetch };
}
