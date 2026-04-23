import { create } from "zustand";
import { persist } from "zustand/middleware";

export type IngredienteExcluido = { id: number; nombre: string };

export type CartItem = {
  productoId: number;
  nombre: string;
  precioUnitario: number;
  cantidad: number;
  /** IDs de ingredientes excluidos (ordenados en persistencia). Vacío = sin exclusiones. */
  personalizacion: number[];
  /** Misma información con nombre para la UI. */
  ingredientesExcluidos: IngredienteExcluido[];
  imagen_url?: string | null;
};

export type ProductoParaCarrito = {
  id: number;
  nombre: string;
  precio: number;
  imagen_url: string | null;
};

export function cartLineKey(productoId: number, personalizacion: number[] | undefined): string {
  const sorted = [...(personalizacion ?? [])].sort((a, b) => a - b);
  return `${productoId}-${sorted.join(",")}`;
}

function normalizePersonalizacion(exclusiones: IngredienteExcluido[] | undefined): {
  personalizacion: number[];
  ingredientesExcluidos: IngredienteExcluido[];
} {
  const ex = exclusiones ?? [];
  const personalizacion = [...ex.map((e) => e.id)].sort((a, b) => a - b);
  return { personalizacion, ingredientesExcluidos: ex };
}

function findLineIndex(
  items: CartItem[],
  productoId: number,
  personalizacion: number[] | undefined,
): number {
  const key = cartLineKey(productoId, personalizacion);
  return items.findIndex((i) => cartLineKey(i.productoId, i.personalizacion) === key);
}

type CartState = {
  items: CartItem[];
  addItem: (
    producto: ProductoParaCarrito,
    cantidad: number,
    exclusiones?: IngredienteExcluido[],
  ) => void;
  increaseItem: (productoId: number, personalizacion?: number[]) => void;
  decreaseItem: (productoId: number, personalizacion?: number[]) => void;
  removeItem: (productoId: number, personalizacion?: number[]) => void;
  clearCart: () => void;
};

// el carrito se guarda en localStorage automaticamente
export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      addItem: (producto, cantidad, exclusiones) => {
        const { personalizacion, ingredientesExcluidos } = normalizePersonalizacion(exclusiones);
        const qty = Math.max(1, Math.min(99, Math.floor(cantidad)));
        const prev = get().items;
        const idx = findLineIndex(prev, producto.id, personalizacion);
        if (idx === -1) {
          set({
            items: [
              ...prev,
              {
                productoId: producto.id,
                nombre: producto.nombre,
                precioUnitario: producto.precio,
                cantidad: qty,
                personalizacion,
                ingredientesExcluidos,
                imagen_url: producto.imagen_url,
              },
            ],
          });
          return;
        }
        const next = [...prev];
        next[idx] = { ...next[idx], cantidad: next[idx].cantidad + qty };
        set({ items: next });
      },
      increaseItem: (productoId, personalizacion) => {
        const prev = get().items;
        const idx = findLineIndex(prev, productoId, personalizacion);
        if (idx === -1) return;
        const next = [...prev];
        next[idx] = { ...next[idx], cantidad: Math.min(99, next[idx].cantidad + 1) };
        set({ items: next });
      },
      decreaseItem: (productoId, personalizacion) => {
        const prev = get().items;
        const idx = findLineIndex(prev, productoId, personalizacion);
        if (idx === -1) return;
        const key = cartLineKey(productoId, personalizacion);
        const actual = prev[idx].cantidad;
        if (actual <= 1) {
          set({
            items: prev.filter((i) => cartLineKey(i.productoId, i.personalizacion) !== key),
          });
          return;
        }
        const next = [...prev];
        next[idx] = { ...next[idx], cantidad: actual - 1 };
        set({ items: next });
      },
      removeItem: (productoId, personalizacion) => {
        const key = cartLineKey(productoId, personalizacion);
        set({
          items: get().items.filter((i) => cartLineKey(i.productoId, i.personalizacion) !== key),
        });
      },
      clearCart: () => set({ items: [] }),
    }),
    {
      name: "foodstore-cart",
      partialize: (s) => ({ items: s.items }),
      onRehydrateStorage: () => (state) => {
        if (!state?.items) return;
        state.items = state.items.map((i) => ({
          ...i,
          personalizacion: Array.isArray(i.personalizacion) ? [...i.personalizacion].sort((a, b) => a - b) : [],
          ingredientesExcluidos: Array.isArray(i.ingredientesExcluidos) ? i.ingredientesExcluidos : [],
        }));
      },
    },
  ),
);
