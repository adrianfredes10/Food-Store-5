import { useEffect, useState } from "react";

import { useCartStore } from "@/shared/store/cart-store";

/** Evita redirigir antes de que Zustand rehidrate el carrito desde localStorage. */
export function useCartHydrated() {
  const [hydrated, setHydrated] = useState(() => useCartStore.persist.hasHydrated());

  useEffect(() => {
    if (useCartStore.persist.hasHydrated()) {
      setHydrated(true);
      return;
    }
    return useCartStore.persist.onFinishHydration(() => {
      setHydrated(true);
    });
  }, []);

  return hydrated;
}
