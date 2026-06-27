import { useCallback, useEffect, useState } from "react";
import { useAuth } from "./useAuth";

export function useFieldDefs() {
  const { token } = useAuth();
  const [fieldDefs, setFieldDefs] = useState([]);
  const [loading, setLoading]     = useState(true);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/field-definitions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setFieldDefs(data);
      }
    } catch {
      // non-fatal
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  return { fieldDefs, loading, reload: load };
}
