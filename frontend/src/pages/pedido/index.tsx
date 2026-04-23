import axios from "axios";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, CreditCard, Crosshair, MapPin, Package, AlertTriangle } from "lucide-react";

import {
  useCancelarPedido,
  usePedidoDetalle,
  usePedidoHistorial,
} from "@/features/pedidos";
import { useIniciarCheckout } from "@/features/pagos";
import { apiErrorDetail } from "@/shared/api/apiErrorDetail";
import { ConfirmDialog, SkeletonPedidoDetalle, EstadoBadge, FormField, LoadingButton } from "@/shared/ui";

function formatMoney(value: number) {
  return value.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 });
}

function formatHistorialFecha(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function labelFormaPago(codigo: string | null): string {
  if (!codigo) return "—";
  if (codigo === "MERCADOPAGO") return "Mercado Pago";
  return codigo;
}

export function PedidoPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [cancelOpen, setCancelOpen] = useState(false);
  const [motivoCancel, setMotivoCancel] = useState("");

  const pedidoId = useMemo(() => {
    const n = Number(id);
    return Number.isFinite(n) && n >= 1 ? n : null;
  }, [id]);

  // cargo los datos del back
  const {
    data: pedido,
    isLoading,
    isError,
    error,
    refetch,
  } = usePedidoDetalle(pedidoId);
  const { data: historialRaw = [] } = usePedidoHistorial(pedidoId);
  const cancelMutation = useCancelarPedido();
  const iniciarCheckout = useIniciarCheckout();

  const [searchParams] = useSearchParams();
  const statusMP = searchParams.get("status");

  useEffect(() => {
    if (statusMP && pedidoId) {
      if (statusMP === "approved") {
        toast.success("¡Pago aprobado! Tu pedido está confirmado.");
      } else if (statusMP === "rejected") {
        toast.error("El pago fue rechazado. Podés intentar de nuevo.");
      } else if (statusMP === "pending") {
        toast.info("Tu pago está pendiente de acreditación.");
      }
      // Limpiar query param de la URL
      navigate(`/pedido/${pedidoId}`, { replace: true });
    }
  }, [statusMP, pedidoId, navigate]);

  // ordeno el historial de más reciente a más viejo
  const historialOrdenado = useMemo(() => {
    return [...historialRaw].sort(
      (a, b) => new Date(b.registrado_en).getTime() - new Date(a.registrado_en).getTime(),
    );
  }, [historialRaw]);

  const subtotalItems = useMemo(() => {
    if (!pedido?.detalles?.length) return 0;
    return pedido.detalles.reduce((acc, d) => acc + Number(d.subtotal), 0);
  }, [pedido]);

  const es404 = axios.isAxiosError(error) && error.response?.status === 404;
  const pendiente = pedido?.estado === "PENDIENTE";

  if (pedidoId === null) {
    return (
      <div className="mx-auto max-w-2xl py-16 text-center fade-in md:py-24 px-4">
        <div className="mb-6 flex justify-center text-muted">
            <AlertTriangle strokeWidth={1} size={64} className="opacity-50" />
        </div>
        <h1 className="mb-4 font-outfit text-2xl font-black text-primary md:text-4xl">
          Pedido no encontrado
        </h1>
        <p className="mb-10 text-sm font-medium text-muted">
          El enlace no es válido o el pedido no existe.
        </p>
        <Link
          to="/mis-pedidos"
          className="inline-flex rounded-xl bg-primary px-8 py-3.5 text-sm font-bold text-white hover:bg-primary-hover active:scale-95 transition-all shadow-sm"
        >
          Ir a mis pedidos
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto min-w-0 max-w-6xl w-full py-4 md:py-8 fade-in px-4 lg:px-0">
      <Link
        to="/mis-pedidos"
        className="mb-6 md:mb-8 inline-flex items-center gap-2 text-sm font-bold text-muted transition-colors hover:text-primary"
      >
        <ArrowLeft size={16} /> Volver a mis pedidos
      </Link>

      {isLoading && <SkeletonPedidoDetalle />}

      {isError && !isLoading && (
        <div className="rounded-2xl border border-border bg-white p-8 text-center shadow-sm max-w-md mx-auto mt-12">
          {es404 ? (
            <>
              <h1 className="mb-4 text-xl font-bold text-primary">
                Pedido no encontrado
              </h1>
              <p className="mb-8 text-sm text-muted">
                No pudimos encontrar este pedido o no pertenece a tu cuenta.
              </p>
              <Link
                to="/mis-pedidos"
                className="inline-block rounded-xl bg-primary px-6 py-3 text-sm font-bold text-white hover:bg-primary-hover shadow-sm"
              >
                Mis pedidos
              </Link>
            </>
          ) : (
            <>
              <h2 className="mb-4 text-lg font-bold text-primary">
                Error al cargar el pedido
              </h2>
              <p className="mb-8 text-sm text-muted">
                {axios.isAxiosError(error) && error.response?.status === 401
                  ? "Iniciá sesión para ver tu pedido."
                  : apiErrorDetail(error, "No se pudo cargar el pedido.")}
              </p>
              <button
                type="button"
                onClick={() => void refetch()}
                className="rounded-xl bg-primary px-6 py-3 text-sm font-bold text-white hover:bg-primary-hover shadow-sm"
              >
                Reintentar
              </button>
            </>
          )}
        </div>
      )}

      {pedido && !isLoading && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-start">
            
            {/* Header / Title (Full width) */}
            <header className="lg:col-span-12 flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-center sm:justify-between order-first mb-2 lg:mb-0">
                <h1 className="font-outfit text-3xl font-black text-primary md:text-5xl tracking-tight">
                Pedido #{pedido.id}
                </h1>
                <div className="flex items-center gap-4">
                    <span className="text-sm font-bold text-muted">{formatHistorialFecha(pedido.created_at)}</span>
                    <EstadoBadge estado={pedido.estado} />
                </div>
            </header>

            {/* Left Column: General Info (Order 2 on mobile, 1 on desktop) lg:col-span-7 */}
            <div className="lg:col-span-7 space-y-6 order-2 lg:order-1">
                {/* Estado/Historial */}
                <section className="rounded-2xl border border-border bg-white p-6 shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-6 opacity-5 text-accent pointer-events-none">
                        <Crosshair size={120} />
                    </div>
                    <div className="relative z-10">
                        <h2 className="text-sm font-bold text-primary uppercase tracking-widest mb-6 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-accent"></span> Estado del pedido
                        </h2>
                        
                        <div className="space-y-6">
                            {historialOrdenado.map((h, i) => (
                                <div key={h.id} className="flex gap-4 relative">
                                    <div className="relative flex flex-col items-center">
                                        <div className={`w-3 h-3 rounded-full shrink-0 z-10 ${i === 0 ? 'bg-accent shadow-[0_0_0_4px_var(--color-bgSecondary)]' : 'bg-muted'}`}></div>
                                        {i < historialOrdenado.length - 1 && (
                                            <div className="absolute top-3 bottom-[-24px] w-0.5 bg-border -z-0"></div>
                                        )}
                                    </div>
                                    <div className="-mt-1.5 flex-1 pb-4">
                                        <span className={`text-sm font-bold block capitalize ${i === 0 ? 'text-primary' : 'text-muted'}`}>
                                            {h.estado_nuevo.replace(/_/g, " ").toLowerCase()}
                                        </span>
                                        <span className="text-xs font-medium text-muted mt-1 block">
                                            {formatHistorialFecha(h.registrado_en)}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Entrega y Pago */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <section className="rounded-2xl border border-border bg-bg-secondary p-6 shadow-sm">
                        <h3 className="mb-4 text-xs font-bold uppercase tracking-widest text-muted flex items-center gap-2">
                            <MapPin size={16} /> Entrega
                        </h3>
                        <p className="font-bold text-primary mb-1">
                            {pedido.dir_alias ?? "Dirección de entrega"}
                        </p>
                        <p className="text-sm text-muted leading-relaxed">
                            {pedido.dir_linea1 ?? "—"}
                        </p>
                    </section>

                    <section className="rounded-2xl border border-border bg-bg-secondary p-6 shadow-sm">
                        <h3 className="mb-4 text-xs font-bold uppercase tracking-widest text-muted flex items-center gap-2">
                             <CreditCard size={16} /> Pago
                        </h3>
                        <p className="font-bold text-primary mb-1">
                            {labelFormaPago(pedido.forma_pago_codigo)}
                        </p>
                        <p className="text-sm text-muted">
                           {formatMoney(Number(pedido.total))}
                        </p>
                    </section>
                </div>
                
                {/* Actions */}
                {pendiente && (
                    <div className="flex flex-col gap-4 sm:flex-row mt-6 pt-6 border-t border-border">
                        <LoadingButton
                            type="button"
                            isLoading={iniciarCheckout.isPending}
                            onClick={() => pedido && iniciarCheckout.mutate(pedido.id)}
                            className="flex-1 rounded-xl bg-accent px-6 py-4 text-sm font-bold text-white shadow-sm hover:bg-accent-hover transition-colors active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Pagar ahora
                        </LoadingButton>
                        <button
                            type="button"
                            onClick={() => {
                                setMotivoCancel("");
                                setCancelOpen(true);
                            }}
                            className="flex-1 rounded-xl border border-danger/30 text-danger bg-danger/5 px-6 py-4 text-sm font-bold shadow-sm hover:bg-danger/10 transition-colors active:scale-95"
                        >
                            Cancelar pedido
                        </button>
                    </div>
                )}
            </div>

            {/* Right Column: Items Detalle (Order 1 on mobile, 2 on desktop) lg:col-span-5 */}
            <div className="lg:col-span-5 order-1 lg:order-2 lg:sticky lg:top-24 mt-2 lg:mt-0">
                <section className="rounded-2xl border border-border bg-white p-6 shadow-sm">
                    <h2 className="mb-6 border-b border-border pb-4 text-sm font-bold text-primary uppercase tracking-widest flex items-center gap-2">
                        <Package size={18} className="text-muted" /> Resumen de ítems
                    </h2>
                    <ul className="divide-y divide-border mb-6">
                    {pedido.detalles.map((d) => (
                        <li key={`${d.id}-${d.producto_id}`} className="py-4 first:pt-0">
                        <div className="flex justify-between items-start text-sm gap-4">
                            <div className="flex-1 min-w-0">
                                <p className="font-bold text-primary truncate leading-tight">
                                    {d.nombre_producto}
                                </p>
                                <p className="text-xs text-muted mt-1">Cant: {d.cantidad} × {formatMoney(Number(d.subtotal) / d.cantidad)}</p>
                                {d.personalizacion && d.personalizacion.length > 0 && (
                                <p className="mt-1.5 text-[11px] font-medium text-muted italic">
                                    Sin Ingredientes (Ref: {d.personalizacion.join(", ")})
                                </p>
                                )}
                            </div>
                            <p className="font-bold text-primary shrink-0">
                                {formatMoney(Number(d.subtotal))}
                            </p>
                        </div>
                        </li>
                    ))}
                    </ul>
                    
                    <div className="space-y-3 pt-6 border-t border-border mt-auto">
                        <div className="flex justify-between text-sm">
                            <span className="text-muted font-medium block">Subtotal ítems</span>
                            <span className="font-bold text-primary">{formatMoney(subtotalItems)}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-muted font-medium block">Costo logística</span>
                            <span className="font-bold text-primary">
                            {formatMoney(Number(pedido.costo_envio))}
                            </span>
                        </div>
                        <div className="flex justify-between items-end border-t border-border pt-6 mt-4">
                            <span className="text-base font-bold text-primary">Importe Total</span>
                            <span className="font-outfit text-3xl font-black text-accent tracking-tight">{formatMoney(Number(pedido.total))}</span>
                        </div>
                    </div>
                </section>
            </div>
        </div>
      )}

      <ConfirmDialog
        open={cancelOpen}
        title={`Cancelar pedido #${pedidoId}`}
        destructive
        confirmLabel={cancelMutation.isPending ? "Cancelando..." : "Confirmar cancelación"}
        onCancel={() => {
          setCancelOpen(false);
          setMotivoCancel("");
        }}
        onConfirm={() => {
          const m = motivoCancel.trim();
          if (m.length < 1) {
            toast.error("Por favor, indicá un motivo.");
            return;
          }
          if (pedidoId === null) return;
          cancelMutation.mutate(
            { id: pedidoId, motivo: m },
            {
              onSuccess: () => {
                toast.success("El pedido fue cancelado correctamente.");
                setCancelOpen(false);
                setMotivoCancel("");
              },
              onError: (err) => {
                toast.error(apiErrorDetail(err, "No se pudo cancelar el pedido."));
              },
            },
          );
        }}
      >
        <p className="mb-6 text-sm text-muted">
          ¿Estás seguro que deseas cancelar el pedido <strong className="text-primary">#{pedidoId}</strong>? Esta acción no se puede deshacer.
        </p>
        
        <FormField label="Motivo de la cancelación" error={motivoCancel.trim().length === 0 ? "Requerido" : undefined}>
          <input
            type="text"
            className="w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-medium text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
            value={motivoCancel}
            onChange={(e) => setMotivoCancel(e.target.value)}
            placeholder="Ej: Desistí de la compra"
            minLength={1}
            autoFocus
          />
        </FormField>
      </ConfirmDialog>
    </div>
  );
}
