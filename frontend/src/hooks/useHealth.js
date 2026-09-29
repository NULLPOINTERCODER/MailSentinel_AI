import { useCallback, useEffect, useState } from "react";
import { getDbHealth, getHealth } from "../services/api";

export default function useHealth() {
  const [state, setState] = useState({ loading: true, backend: null, db: null });

  const check = useCallback(async () => {
    setState((s) => ({ ...s, loading: true }));
    const [backend, db] = await Promise.allSettled([getHealth(), getDbHealth()]);
    setState({
      loading: false,
      backend: backend.status === "fulfilled" ? backend.value : null,
      db: db.status === "fulfilled" ? db.value : null,
    });
  }, []);

  useEffect(() => { check(); }, [check]);

  return { ...state, refresh: check };
}
