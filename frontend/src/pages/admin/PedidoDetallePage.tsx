import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import { MoveLeft } from "lucide-react";

import { useAdminPedidoDetalle, useAdminPedidoTransicion } from "@/features/admin";
import { EstadoBadge, LoadingButton } from "@/shared/ui";

const SIGUIENTE: Record<string, string | undefined> = {
  CONFIRMADO: "EN_PREP",
  EN_PREP: "EN_CAMINO",
  EN_CAMINO: "ENTREGADO",
};

function formatMoney(value: string | number) {
  const n = typeof value === "number" ? value : Number.parseFloat(String(value));
  return n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 });
}

export function AdminPedidoDetallePage() {
  const { id } = useParams<{ id: string }>();
  const pedidoId = useMemo(() => {
    const n = Number(id);
    return Number.isFinite(n) && n >= 1 ? n : null;
  }, [id]);

  const { data, isLoading } = useAdminPedidoDetalle(pedidoId);
  const transicion = useAdminPedidoTransicion();

  const siguiente = data ? SIGUIENTE[data.estado] : undefined;

  if (pedidoId === null) {
    return (
      <div className="p-8 rounded-2xl bg-danger/10 border border-danger/20 text-center shadow-sm">
        <p className="text-sm font-bold text-danger uppercase tracking-widest leading-relaxed">
            Identificador de orden no válido.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm font-bold uppercase tracking-widest text-muted animate-pulse">
            Recuperando Detalles de Orden...
        </p>
      </div>
    );
  }

  return (
    <div className="min-w-0 space-y-6 pb-16 sm:space-y-8 sm:pb-20">
      <header className="flex flex-col gap-4 sm:gap-6 md:flex-row md:items-center md:justify-between">
        <Link to="/admin/pedidos" className="group inline-flex items-center gap-3 text-xs font-bold uppercase tracking-widest text-muted transition-all hover:text-primary touch-manipulation">
          <MoveLeft size={16} className="transition-transform group-hover:-translate-x-1" />
          Volver a Pedidos
        </Link>
        <div className="flex flex-wrap items-center gap-3 sm:gap-4">
            <span className="font-outfit text-lg font-black uppercase tracking-tighter text-primary sm:text-xl md:text-2xl">
              Ticket #{pedidoId}
            </span>
            {data && (
                <EstadoBadge estado={data.estado} />
            )}
        </div>
      </header>

      {data && (
        <div className="grid grid-cols-1 items-start gap-6 min-w-0 lg:grid-cols-2 md:gap-8 lg:gap-10">
          <section className="rounded-2xl border border-border bg-white p-6 shadow-sm sm:p-8 md:p-10">
            <h2 className="text-xs font-bold text-muted uppercase tracking-widest font-outfit mb-6 pb-4 border-b border-border">Gestión de Orden</h2>
            
            <div className="space-y-6 mb-8">
                <div className="flex flex-col gap-2 text-muted sm:flex-row sm:items-center sm:justify-between bg-bg-secondary p-6 rounded-xl border border-border">
                    <span className="font-bold text-xs uppercase tracking-widest">Total Abonado</span>
                    <span className="break-words font-outfit text-xl font-black tracking-tighter text-primary sm:text-3xl">
                        {formatMoney(data.total)}
                    </span>
                </div>
            </div>

            {siguiente ? (
                <div className="pt-6 border-t border-border">
                    <LoadingButton
                        type="button"
                        isLoading={transicion.isPending}
                        className="w-full touch-manipulation rounded-xl bg-accent py-4 font-bold text-xs uppercase tracking-widest text-white shadow-sm transition-all hover:bg-accent-hover"
                        onClick={() => transicion.mutate({ pedidoId, estado: siguiente })}
                    >
                        Avanzar a {siguiente}
                    </LoadingButton>
                </div>
            ) : (
                <div className="pt-6 border-t border-border">
                    <div className="w-full text-center rounded-xl bg-bg-secondary py-4 font-bold text-xs uppercase tracking-widest text-muted border border-border">
                        Orden Finalizada
                    </div>
                </div>
            )}
          </section>

          <section className="min-w-0 rounded-2xl border border-border bg-white p-6 shadow-sm sm:p-8 md:p-10">
            <h2 className="mb-6 border-b border-border pb-4 font-outfit text-xs font-bold uppercase tracking-widest text-muted">Contenido del Pedido</h2>
            <ul className="divide-y divide-border">
              {data.detalles.map((d, i) => (
                <li key={i} className="flex min-w-0 flex-col gap-2 py-4">
                    <div className="flex min-w-0 flex-col gap-1 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
                        <span className="min-w-0 break-words text-sm font-bold text-primary">{d.nombre_producto}</span>
                        <span className="shrink-0 text-sm font-black font-outfit text-primary whitespace-nowrap">{formatMoney(d.subtotal)}</span>
                    </div>
                    <p className="text-xs font-bold text-muted uppercase tracking-widest leading-relaxed">
                        {d.cantidad} unid. × {formatMoney(d.precio_unitario_snapshot)}
                    </p>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
