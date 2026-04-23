import { create } from "zustand";

interface UIState {
  cartOpen: boolean;
  sidebarOpen: boolean;
  toggleCart: () => void;
  setCartOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  cartOpen: false,
  sidebarOpen: false,
  toggleCart: () => set((state) => ({ cartOpen: !state.cartOpen })),
  setCartOpen: (open) => set({ cartOpen: open }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
