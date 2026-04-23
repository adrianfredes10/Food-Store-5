import { useEffect, useState } from "react";

import { useAuthStore } from "@/shared/store/auth-store";

/** Evita redirigir a login antes de que Zustand rehidrate el token desde localStorage. */
export function useAuthHydrated() {
  const [hydrated, setHydrated] = useState(() => useAuthStore.persist.hasHydrated());

  useEffect(() => {
    if (useAuthStore.persist.hasHydrated()) {
      setHydrated(true);
      return;
    }
    return useAuthStore.persist.onFinishHydration(() => {
      setHydrated(true);
    });
  }, []);

  return hydrated;
}
