import { useMemo } from "react";
import { useNavigate, Link } from "react-router-dom";
import { MoveLeft, PackageOpen, CreditCard } from "lucide-react";

import { CartItem } from "@/features/carrito/ui/CartItem";
import { useCartStore } from "@/shared/store/cart-store";
import { EmptyState } from "@/shared/ui/EmptyState";

function formatMoney(value: number) {
  return value.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 });
}

export function CarritoPage() {
  const navigate = useNavigate();
  // el carrito se guarda en localStorage automaticamente
  const items = useCartStore((s) => s.items);
  const clearCart = useCartStore((s) => s.clearCart);

  const subtotal = useMemo(() => items.reduce((acc, i) => acc + i.precioUnitario * i.cantidad, 0), [items]);
  const envio = 50;
  const total = subtotal > 0 ? subtotal + envio : 0;

  const hayItems = items.length > 0;
  const estaVacio = !hayItems;

  return (
    <div className="mx-auto w-full max-w-6xl py-4 sm:py-8 lg:py-12 fade-in">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
            <Link to="/" className="flex h-10 w-10 items-center justify-center rounded-full bg-white border border-border text-muted hover:text-primary transition-colors hover:shadow-sm active:scale-95">
                <MoveLeft size={20} />
            </Link>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black text-primary font-outfit uppercase tracking-tight">
              TU CARRITO
            </h1>
        </div>
        {hayItems && (
            <button
              onClick={() => clearCart()}
              className="text-xs sm:text-sm font-bold text-muted hover:text-danger hover:underline transition-colors px-2 py-1 underline-offset-4"
            >
              Vaciar carrito
            </button>
        )}
      </div>

      {estaVacio ? (
        <EmptyState 
            titulo="Tu carrito está vacío" 
            descripcion="Aún no ha seleccionado la excelencia de nuestro catálogo. Descubrí nuestras opciones gourmet y deleitá tu paladar."
            accion={{ label: "Explorar catálogo", href: "/" }}
            icon={PackageOpen}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start relative pb-24 lg:pb-0">
          
          {/* Columna Izquierda: Items (60% en desktop = col-span-7 o 8) */}
          <div className="lg:col-span-7 xl:col-span-8 flex flex-col gap-6">
            <div className="bg-white rounded-2xl md:rounded-[2rem] border border-border shadow-sm p-4 sm:p-6 md:p-8">
                <div className="flex flex-col">
                    {items.map((item) => (
                      <CartItem key={`${item.productoId}-${item.personalizacion.join(",")}`} item={item} />
                    ))}
                </div>
            </div>
          </div>

          {/* Columna Derecha: Resumen (40% en desktop = col-span-5 o 4) */}
          <div className="lg:col-span-5 xl:col-span-4 bg-bg-secondary rounded-2xl md:rounded-[2rem] border border-border p-6 sm:p-8 lg:sticky lg:top-24 shadow-sm">
            <h3 className="text-lg font-bold text-primary mb-6 border-b border-border pb-4">Resumen del Pedido</h3>
            
            <div className="space-y-4 mb-6">
                <div className="flex justify-between items-center text-sm">
                    <span className="text-muted font-medium">Subtotal</span>
                    <span className="font-bold text-primary">{formatMoney(subtotal)}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                    <span className="text-muted font-medium">Costo de envío</span>
                    <span className="font-bold text-primary">{formatMoney(envio)}</span>
                </div>
            </div>

            <div className="border-t border-border pt-6 mb-8 flex justify-between items-end">
                <span className="text-base font-bold text-primary">Total</span>
                <span className="text-3xl font-black text-accent tracking-tight">{formatMoney(total)}</span>
            </div>

            {/* Check out button for desktop/tablet */}
            <div className="hidden lg:block">
                <button
                    onClick={() => navigate("/checkout")}
                    className="w-full py-4 bg-accent text-white font-bold text-lg rounded-xl flex items-center justify-center gap-3 hover:bg-accent-hover transition-all active:scale-95 shadow-md shadow-accent/20"
                >
                    <CreditCard size={20} />
                    Ir al checkout
                </button>
            </div>
          </div>

          {/* Floating Checkout Button for Mobile */}
          <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-border shadow-[0_-10px_40px_rgba(0,0,0,0.1)] lg:hidden z-40">
             <button
                onClick={() => navigate("/checkout")}
                className="w-full py-3.5 bg-accent text-white font-bold text-base rounded-xl flex items-center justify-center gap-2 hover:bg-accent-hover active:scale-95 shadow-md shadow-accent/20"
            >
                <CreditCard size={20} />
                Confirmar compra ({formatMoney(total)})
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
