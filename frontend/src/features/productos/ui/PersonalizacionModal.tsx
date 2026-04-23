import { useEffect, useMemo, useState } from "react";

import { useIngredientesDeProducto } from "@/features/admin/hooks/useAdminIngredientes";

export interface PersonalizacionModalProps {
  producto: {
    id: number;
    nombre: string;
    precio: number;
    imagen_url: string | null;
  };
  onClose: () => void;
  onConfirm: (cantidad: number, exclusiones: { id: number; nombre: string }[]) => void;
}

function formatMoney(value: number) {
  return value.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 });
}

export function PersonalizacionModal({ producto, onClose, onConfirm }: PersonalizacionModalProps) {
  const { data: ingredientes = [], isLoading, isError } = useIngredientesDeProducto(producto.id);
  const [cantidad, setCantidad] = useState(1);
  const [includedMap, setIncludedMap] = useState<Record<number, boolean>>({});

  // solo muestro la lista si cargaron bien los ingredientes
  const showIngredientList = !isLoading && !isError && ingredientes.length > 0;

  // bloqueo el scroll del body mientras el modal está abierto
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  useEffect(() => {
    if (!ingredientes.length) return;
    setIncludedMap((prev) => {
      const next = { ...prev };
      for (const ing of ingredientes) {
        if (next[ing.ingrediente_id] === undefined) {
          next[ing.ingrediente_id] = true;
        }
      }
      return next;
    });
  }, [ingredientes]);

  // armo la lista de ingredientes que el usuario quitó
  const exclusiones = useMemo(() => {
    return ingredientes
      .filter((ing) => ing.es_removible && includedMap[ing.ingrediente_id] === false)
      .map((ing) => ({ id: ing.ingrediente_id, nombre: ing.nombre }));
  }, [ingredientes, includedMap]);

  const toggleRemovible = (ingredienteId: number, esRemovible: boolean) => {
    if (!esRemovible) return;
    setIncludedMap((m) => ({ ...m, [ingredienteId]: !m[ingredienteId] }));
  };

  const handleConfirm = () => {
    onConfirm(cantidad, exclusiones);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="personalizacion-modal-title"
    >
      <div className="max-h-[min(90dvh,100vh)] w-full max-w-md overflow-y-auto overscroll-contain rounded-t-2xl border border-slate-200 bg-white p-5 shadow-lg sm:rounded-lg sm:pb-5 pb-[max(1.25rem,env(safe-area-inset-bottom))]">
        <h2 id="personalizacion-modal-title" className="text-base font-semibold text-slate-900 sm:text-lg pr-8">
          {producto.nombre}
        </h2>
        <p className="mt-1 text-sm font-medium text-slate-700">{formatMoney(producto.precio)}</p>

        <div className="mt-4 flex items-center justify-center gap-4 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
          <button
            type="button"
            className="touch-manipulation rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
            onClick={() => setCantidad((c) => Math.max(1, c - 1))}
            disabled={cantidad <= 1}
            aria-label="Menos cantidad"
          >
            −
          </button>
          <span className="min-w-[2rem] text-center text-sm font-black text-slate-900">{cantidad}</span>
          <button
            type="button"
            className="touch-manipulation rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
            onClick={() => setCantidad((c) => Math.min(99, c + 1))}
            disabled={cantidad >= 99}
            aria-label="Más cantidad"
          >
            +
          </button>
        </div>

        {isLoading && (
          <p className="mt-4 text-xs text-slate-400 font-medium">Cargando ingredientes…</p>
        )}

        {showIngredientList && (
          <ul className="mt-4 space-y-3 border-t border-slate-100 pt-4">
            {ingredientes.map((ing) => {
              const checked = ing.es_removible ? (includedMap[ing.ingrediente_id] !== false) : true;
              const disabled = !ing.es_removible;
              return (
                <li
                  key={ing.ingrediente_id}
                  className="flex flex-wrap items-center gap-2 text-sm text-slate-700"
                >
                  <label className="flex flex-1 cursor-pointer items-center gap-2 min-w-0">
                    <input
                      type="checkbox"
                      className="h-4 w-4 shrink-0 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500 disabled:cursor-not-allowed"
                      checked={checked}
                      disabled={disabled}
                      onChange={() => toggleRemovible(ing.ingrediente_id, ing.es_removible)}
                    />
                    <span className="break-words font-medium">{ing.nombre}</span>
                  </label>
                  {ing.es_alergeno && (
                    <span className="rounded bg-red-600 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                      Alérgeno
                    </span>
                  )}
                  {disabled && (
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Obligatorio</span>
                  )}
                </li>
              );
            })}
          </ul>
        )}

        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onClose}
            className="min-h-11 w-full rounded-md border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 sm:min-h-0 sm:w-auto touch-manipulation"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            className="min-h-11 w-full rounded-md bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 sm:min-h-0 sm:w-auto touch-manipulation"
          >
            Agregar al carrito
          </button>
        </div>
      </div>
    </div>
  );
}
