import { Trash2, Plus, Minus } from "lucide-react";
import type { CartItem as CartItemType } from "@/shared/store/cart-store";
import { useCartStore } from "@/shared/store/cart-store";

type Props = {
  item: CartItemType;
};

function formatMoney(value: number) {
  return value.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 });
}

export function CartItem({ item }: Props) {
  const increaseItem = useCartStore((s) => s.increaseItem);
  const decreaseItem = useCartStore((s) => s.decreaseItem);
  const removeItem = useCartStore((s) => s.removeItem);

  // calculo el precio total de este item
  const subtotal = item.precioUnitario * item.cantidad;
  const pers = item.personalizacion;

  const imgSrc = item.imagen_url ?? null;
  // si la url empieza con http es externa y hay que mandarle el referrer policy
  const esExterna = Boolean(imgSrc && /^https?:\/\//i.test(imgSrc));

  return (
    <div className="group flex flex-col justify-between gap-4 border-b border-border py-4 first:pt-0 last:border-0 last:pb-0 sm:flex-row sm:items-center sm:gap-6 sm:py-6">
      
      {/* Izquierda: Imagen + Info */}
      <div className="flex flex-1 items-start gap-3 md:gap-4 min-w-0">
        <div className="h-[60px] w-[60px] shrink-0 overflow-hidden rounded-lg bg-bg-secondary border border-border">
            {/* si tiene imagen la muestro, sino el placeholder */}
            {imgSrc ? (
              <img
                src={imgSrc}
                alt={item.nombre}
                className="h-full w-full object-cover"
                referrerPolicy={esExterna ? "no-referrer" : undefined}
                loading="lazy"
              />
            ) : (
               <div className="flex h-full w-full items-center justify-center filter grayscale opacity-30 text-xl">🍽️</div>
            )}
        </div>
        
        <div className="flex flex-col min-w-0 flex-1 py-0.5">
          <h4 className="text-sm font-bold text-primary group-hover:text-accent transition-colors truncate">
            {item.nombre}
          </h4>
          {item.ingredientesExcluidos.length > 0 && (
            <p className="text-[10px] text-muted italic line-clamp-1 mt-0.5">
              Sin: {item.ingredientesExcluidos.map((e) => e.nombre).join(", ")}
            </p>
          )}
          <div className="mt-1 flex items-center gap-2 text-[11px] font-medium text-muted">
              <span>{formatMoney(item.precioUnitario)} c/u</span>
          </div>
        </div>
      </div>
      
      {/* Derecha: Controles + Subtotal + Borrar */}
      <div className="flex items-center justify-between gap-4 sm:justify-end sm:gap-6 pl-[72px] sm:pl-0">
        {/* Controles de cantidad */}
        <div className="flex items-center gap-3 rounded-lg border border-border bg-bg-secondary px-2 py-1.5 shrink-0">
          <button
            type="button"
            className="p-1 text-muted transition-colors hover:text-primary disabled:opacity-30 active:scale-95"
            onClick={() => decreaseItem(item.productoId, pers)}
            disabled={item.cantidad <= 1}
          >
            <Minus size={14} strokeWidth={2.5} />
          </button>
          <span className="min-w-[20px] text-center text-xs font-bold text-primary">{item.cantidad}</span>
          <button
            type="button"
            className="p-1 text-muted transition-colors hover:text-primary active:scale-95"
            onClick={() => increaseItem(item.productoId, pers)}
          >
            <Plus size={14} strokeWidth={2.5} />
          </button>
        </div>

        {/* Subtotal */}
        <div className="flex items-center sm:items-end flex-col shrink-0">
            <span className="text-[10px] sm:hidden font-bold tracking-widest text-muted uppercase">Subtotal</span>
            <p className="text-sm sm:text-base font-bold text-primary tracking-tight">
                {formatMoney(subtotal)}
            </p>
        </div>

        {/* botón para sacar el item del carrito */}
        <button
          type="button"
          onClick={() => removeItem(item.productoId, pers)}
          className="text-muted hover:text-danger hover:bg-danger/10 transition-colors p-2 rounded-lg active:scale-90 shrink-0"
          title="Eliminar del carrito"
        >
          <Trash2 size={18} />
        </button>
      </div>
    </div>
  );
}
