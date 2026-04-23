import { create } from "zustand";

export type CheckoutStep = "idle" | "creating" | "paying" | "success" | "failed";

type PaymentState = {
  checkoutStep: CheckoutStep;
  pedidoId: number | null;
  preferenceId: string | null;
  paymentStatus: string | null;
  error: string | null;
  startCheckout: (pedidoId: number) => void;
  setPreference: (preferenceId: string) => void;
  updatePaymentStatus: (status: string) => void;
  setError: (error: string) => void;
  resetPayment: () => void;
};

const initial: Pick<
  PaymentState,
  "checkoutStep" | "pedidoId" | "preferenceId" | "paymentStatus" | "error"
> = {
  checkoutStep: "idle",
  pedidoId: null,
  preferenceId: null,
  paymentStatus: null,
  error: null,
};

// manejo el estado del checkout con zustand
export const usePaymentStore = create<PaymentState>((set) => ({
  ...initial,
  startCheckout: (pedidoId) =>
    set({
      checkoutStep: "creating",
      pedidoId,
      error: null,
    }),
  setPreference: (preferenceId) =>
    set({
      checkoutStep: "paying",
      preferenceId,
    }),
  updatePaymentStatus: (status) =>
    set((s) => {
      let checkoutStep = s.checkoutStep;
      if (status === "approved") checkoutStep = "success";
      else if (status === "rejected") checkoutStep = "failed";
      return { paymentStatus: status, checkoutStep };
    }),
  setError: (error) =>
    set({
      checkoutStep: "failed",
      error,
    }),
  resetPayment: () => set(initial),
}));
