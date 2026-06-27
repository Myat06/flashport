import { useEffect, useRef, useState } from "react";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const WS  = import.meta.env.VITE_WS_URL  ?? "ws://localhost:8000";

function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}

// Normalize a SyncResponse (declaration_id) to match DeclarationOut shape (id)
function normalizeWsDeclaration(data) {
  return {
    ...data,
    id: data.declaration_id ?? data.id,
  };
}

export function useDeclarations(token) {
  const [declarations, setDeclarations] = useState([]);
  const [connected, setConnected]       = useState(false);
  const [loading, setLoading]           = useState(true);
  const [redLaneAlert, setRedLaneAlert] = useState(null); // {id, document_type, risk_score}
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
          const item = normalizeWsDeclaration(msg.data);
          setDeclarations((prev) => {
            const exists = prev.some((d) => d.id === item.id);
            return exists ? prev : [item, ...prev];
          });
          // Alert manager when a red-lane document arrives
          if (item.risk_badge === "red") {
            setRedLaneAlert({
              id:            item.id,
              document_type: item.document_type,
              risk_score:    item.risk_score,
            });
          }
        }
      };
    };

    connect();
    return () => wsRef.current?.close();
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const updateField = async (declarationId, fieldName, fieldValue) => {
    await fetch(`${API}/declarations/${declarationId}/field`, {
      method:  "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders(token) },
      body:    JSON.stringify({ field_name: fieldName, field_value: fieldValue, reviewed_by: "manager" }),
    });
    setDeclarations((prev) =>
      prev.map((d) => {
        if (d.id !== declarationId) return d;
        return { ...d, extracted_fields: { ...d.extracted_fields, [fieldName]: fieldValue } };
      })
    );
  };

  const submitToCeisa = async (declarationId) => {
    const res = await fetch(`${API}/ceisa/submit`, {
      method:  "POST",
      headers: { "Content-Type": "application/json", ...authHeaders(token) },
      body:    JSON.stringify({ declaration_id: declarationId, submitted_by: "manager" }),
    });
    return res.json();
  };

  const reviewDeclaration = async (declarationId, status, note) => {
    await fetch(`${API}/declarations/${declarationId}/review`, {
      method:  "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders(token) },
      body:    JSON.stringify({ status, note, reviewed_by: "manager" }),
    });
    setDeclarations((prev) =>
      prev.map((d) => {
        if (d.id !== declarationId) return d;
        return {
          ...d,
          review_status: status,
          review_note:   note,
          reviewed_by:   "manager",
          reviewed_at:   new Date().toISOString(),
        };
      })
    );
  };

  const dismissRedAlert = () => setRedLaneAlert(null);

  return {
    declarations, connected, loading,
    redLaneAlert, dismissRedAlert,
    updateField, submitToCeisa, reviewDeclaration, refetch,
  };
}
