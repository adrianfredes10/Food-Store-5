import { useEffect, useMemo, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { CopySlash } from "lucide-react";

import { useAuthHydrated } from "@/features/auth";
import { useMisPedidos } from "@/features/pedidos";
import { useAuthStore } from "@/shared/store/auth-store";
import { SkeletonTable, EmptyState, EstadoBadge } from "@/shared/ui";

const ESTADOS = [
  "TODOS",
  "PENDIENTE",
  "CONFIRMADO",
  "EN_PREP",
  "EN_CAMINO",
  "ENTREGADO",
  "CANCELADO",
] as const;

type FiltroEstado = (typeof ESTADOS)[number];

function formatMoney(value: number) {
  return value.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 });
}

function formatFecha(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function MisPedidosPage() {
  const hydrated = useAuthHydrated();
  const token = useAuthStore((s) => s.access_token);
  const [page, setPage] = useState(1);
  const [filtroEstado, setFiltroEstado] = useState<FiltroEstado>("TODOS");

  // cuando cambia el filtro vuelvo a la primer página
  useEffect(() => {
    setPage(1);
  }, [filtroEstado]);

  const params = useMemo(
    () => ({
      page,
      size: 10,
      ...(filtroEstado !== "TODOS" ? { estado: filtroEstado } : {}),
    }),
    [page, filtroEstado],
  );

  // cargo los pedidos del back con los filtros aplicados
  const { data, isLoading, isError, error, refetch } = useMisPedidos(params);

  if (!hydrated) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="animate-pulse text-[10px] font-black uppercase tracking-[0.3em] text-slate-300">
          Sincronizando...
        </p>
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  const items = data?.items ?? [];
  const pages = data?.pages ?? 0;
  const total = data?.total ?? 0;

  return (
    <div className="mx-auto min-w-0 max-w-6xl fade-in py-4 md:py-8 w-full px-2 sm:px-0">
      <header className="mb-6 md:mb-10 text-center md:text-left flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
            <h1 className="text-2xl md:text-4xl font-black text-primary font-outfit uppercase tracking-tight mb-1 md:mb-2">
            Mis pedidos
            </h1>
            <p className="text-xs font-bold uppercase tracking-widest text-muted">
            Historial y seguimiento de tus compras
            </p>
        </div>

        <div className="flex items-end gap-3 justify-center md:justify-end">
            <label className="block w-full max-w-[200px]">
                <span className="mb-1 block text-left text-[10px] font-bold uppercase tracking-widest text-muted">
                Filtrar por Estado
                </span>
                <select
                className="w-full rounded-xl border border-border bg-bg-secondary px-3 py-2.5 text-sm font-bold text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent appearance-none dropdown-icon"
                value={filtroEstado}
                onChange={(e) => setFiltroEstado(e.target.value as FiltroEstado)}
                >
                {ESTADOS.map((e) => (
                    <option key={e} value={e}>
                    {e === "TODOS" ? "Todos los pedidos" : e.replace(/_/g, " ")}
                    </option>
                ))}
                </select>
            </label>
        </div>
      </header>

      {isLoading && (
        <SkeletonTable />
      )}

      {isError && !isLoading && (
        <div className="rounded-2xl border border-danger/20 bg-danger/5 p-8 text-center max-w-md mx-auto mt-12">
          <p className="mb-4 text-sm font-bold text-danger">
            {error instanceof Error ? error.message : "No se pudieron cargar los pedidos."}
          </p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="rounded-xl bg-danger px-6 py-3 text-sm font-bold text-white hover:bg-danger/80"
          >
            Reintentar
          </button>
        </div>
      )}

      {!isLoading && !isError && items.length === 0 && (
        <div className="mt-8">
            <EmptyState 
                titulo={filtroEstado === "TODOS" ? "Todavía no realizaste ningún pedido" : "No hay pedidos con este estado"}
                descripcion={filtroEstado === "TODOS" ? "Explorá nuestro catálogo y descubrí una selección exclusiva pensada para vos." : "Probá cambiando el filtro o seleccioná 'Todos los pedidos'."}
                accion={filtroEstado === "TODOS" ? { label: "Ir al catálogo", href: "/" } : undefined}
                icon={CopySlash}
            />
        </div>
      )}

      {!isLoading && !isError && items.length > 0 && (
        <>
            {/* Desktop Table View */}
            <div className="hidden md:block overflow-hidden rounded-2xl border border-border bg-white shadow-sm">
                <table className="w-full min-w-[640px] text-left">
                    <thead className="bg-bg-secondary border-b border-border">
                        <tr>
                        <th className="px-6 py-4 text-xs font-bold text-muted uppercase tracking-wider">Nº Pedido</th>
                        <th className="px-6 py-4 text-xs font-bold text-muted uppercase tracking-wider">Fecha</th>
                        <th className="px-6 py-4 text-xs font-bold text-muted uppercase tracking-wider">Estado</th>
                        <th className="px-6 py-4 text-xs font-bold text-muted uppercase tracking-wider">Total</th>
                        <th className="px-6 py-4 text-right text-xs font-bold text-muted uppercase tracking-wider">Acción</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {items.map((p) => (
                        <tr key={p.id} className="hover:bg-primary/5 transition-colors group">
                            <td className="px-6 py-4 text-sm font-bold text-primary group-hover:text-accent font-outfit">#{p.id}</td>
                            <td className="px-6 py-4 text-sm text-muted">{formatFecha(p.created_at)}</td>
                            <td className="px-6 py-4">
                                <EstadoBadge estado={p.estado} />
                            </td>
                            <td className="px-6 py-4 text-sm font-bold text-primary font-outfit">{formatMoney(Number(p.total))}</td>
                            <td className="px-6 py-4 text-right">
                            <Link to={`/pedido/${p.id}`} className="text-sm font-bold text-accent hover:text-accent-hover hover:underline transition-all">Ver detalle</Link>
                            </td>
                        </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Mobile Cards View */}
            <div className="flex flex-col gap-4 md:hidden">
                <p className="text-xs font-bold text-muted uppercase tracking-widest">{total} pedido(s) encontrado(s)</p>
                {items.map((p) => (
                    <Link to={`/pedido/${p.id}`} key={p.id} className="block bg-white rounded-2xl border border-border p-5 shadow-sm active:scale-95 transition-transform flex flex-col gap-4 relative overflow-hidden">
                        <div className="flex justify-between items-start">
                            <div className="space-y-1">
                                <span className="text-lg font-black text-primary font-outfit">#{p.id}</span>
                                <span className="text-xs text-muted block capitalize">{formatFecha(p.created_at)}</span>
                            </div>
                            <EstadoBadge estado={p.estado} />
                        </div>
                        <div className="flex justify-between items-center pt-4 border-t border-border mt-auto">
                            <span className="text-xs font-bold uppercase text-muted tracking-widest">Importe Total</span>
                            <span className="text-xl font-black text-accent tracking-tight">{formatMoney(Number(p.total))}</span>
                        </div>
                    </Link>
                ))}
            </div>

          {pages > 1 && (
            <div className="mt-8 flex items-center justify-center gap-4">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="rounded-xl border border-border bg-white px-5 py-2.5 text-xs font-bold uppercase tracking-widest text-primary hover:bg-bg-secondary disabled:opacity-40 transition-colors shadow-sm"
              >
                Anterior
              </button>
              <span className="text-xs font-bold text-muted">
                Página {page} de {pages}
              </span>
              <button
                type="button"
                disabled={page >= pages}
                onClick={() => setPage((p) => Math.min(pages, p + 1))}
                className="rounded-xl border border-accent bg-accent/5 px-5 py-2.5 text-xs font-bold uppercase tracking-widest text-accent hover:bg-accent/10 disabled:opacity-40 transition-colors shadow-sm"
              >
                Siguiente
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
