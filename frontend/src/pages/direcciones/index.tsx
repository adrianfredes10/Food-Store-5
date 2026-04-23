import { Star, MapPin, MapPinned } from "lucide-react";
import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { toast } from "sonner";

import { useAuthHydrated } from "@/features/auth";
import { useDirecciones, useDireccionesMutations, useMarcarPrincipal } from "@/features/direcciones";
import { useAuthStore } from "@/shared/store/auth-store";
import { ConfirmDialog, FormField, LoadingButton, EmptyState } from "@/shared/ui";

const emptyForm = {
  alias: "",
  calle: "",
  numero: "",
  piso_dpto: "",
  ciudad: "",
  codigo_postal: "",
  referencias: "",
  es_principal: false,
};

export function DireccionesPage() {
  const hydrated = useAuthHydrated();
  const token = useAuthStore((s) => s.access_token);
  // cargo las direcciones guardadas del usuario
  const { data = [], isLoading } = useDirecciones();
  const { crear, actualizar, eliminar } = useDireccionesMutations();
  const marcarPrincipal = useMarcarPrincipal();
  const [form, setForm] = useState(emptyForm);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);

  if (!hydrated) {
    return (
      <div className="flex items-center justify-center py-12 md:py-20">
        <p className="text-sm font-bold uppercase tracking-widest text-muted animate-pulse">Sincronizando...</p>
      </div>
    );
  }
  
  if (!token) return <Navigate to="/login" replace />;

  return (
    <div className="mx-auto max-w-6xl w-full py-4 sm:py-8 lg:py-12 fade-in px-4 lg:px-0">
      <header className="mb-6 md:mb-12 text-center md:text-left flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
            <h1 className="text-2xl md:text-4xl font-black text-primary font-outfit uppercase tracking-tight mb-2">
            Direcciones
            </h1>
            <p className="text-xs font-bold uppercase tracking-widest text-muted">Gestión de puntos de entrega</p>
        </div>
        <Link
            to="/mis-pedidos"
            className="md:shrink-0 inline-block text-xs font-bold uppercase tracking-widest text-accent hover:text-accent-hover hover:underline underline-offset-4 transition-colors"
        >
            Mis pedidos
        </Link>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start relative pb-8">
        {/* Form Column -> lg:col-span-5 */}
        <div className="lg:col-span-5 space-y-6 lg:sticky lg:top-24 order-2 lg:order-1">
            <section className="bg-white rounded-2xl border border-border p-6 sm:p-8 shadow-sm">
                <h2 className="text-sm font-bold text-primary uppercase tracking-widest mb-6 border-b border-border pb-4 flex items-center gap-2">
                    <MapPin size={18} className="text-muted" /> 
                    {editingId ? "Editar Dirección" : "Nueva Dirección"}
                </h2>
                
                <form
                    className="space-y-5"
                    onSubmit={(e) => {
                        e.preventDefault();
                        if (!form.calle.trim() || !form.numero.trim() || !form.ciudad.trim() || !form.codigo_postal.trim()) return;
                        
                        const payload = {
                            alias: form.alias.trim() || null,
                            calle: form.calle.trim(),
                            numero: form.numero.trim(),
                            piso_dpto: form.piso_dpto.trim() || null,
                            ciudad: form.ciudad.trim(),
                            codigo_postal: form.codigo_postal.trim(),
                            referencias: form.referencias.trim() || null,
                            es_principal: form.es_principal,
                        };

                        // si hay id es edición, sino es creación nueva
                        if (editingId) {
                            actualizar.mutate({ id: editingId, body: payload }, {
                                onSuccess: () => {
                                    setEditingId(null);
                                    setForm(emptyForm);
                                }
                            });
                        } else {
                            crear.mutate(payload, {
                                onSuccess: () => setForm(emptyForm)
                            });
                        }
                    }}
                >
                    <FormField label="Alias (ej: Casa, Trabajo)">
                        <input
                            className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all placeholder:text-muted/50"
                            placeholder="Dejar en blanco para usar la calle"
                            value={form.alias}
                            onChange={(e) => setForm((f) => ({ ...f, alias: e.target.value }))}
                        />
                    </FormField>

                    <div className="grid grid-cols-2 gap-4">
                        <FormField label="Calle *" className="col-span-1">
                            <input
                                required
                                className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                                value={form.calle}
                                onChange={(e) => setForm((f) => ({ ...f, calle: e.target.value }))}
                            />
                        </FormField>
                        <FormField label="Número *" className="col-span-1">
                            <input
                                required
                                className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                                value={form.numero}
                                onChange={(e) => setForm((f) => ({ ...f, numero: e.target.value }))}
                            />
                        </FormField>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <FormField label="Piso / Dpto" className="col-span-1">
                            <input
                                className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                                value={form.piso_dpto}
                                onChange={(e) => setForm((f) => ({ ...f, piso_dpto: e.target.value }))}
                            />
                        </FormField>
                        <FormField label="Ciudad *" className="col-span-1">
                            <input
                                required
                                className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                                value={form.ciudad}
                                onChange={(e) => setForm((f) => ({ ...f, ciudad: e.target.value }))}
                            />
                        </FormField>
                    </div>

                    <FormField label="Código Postal *">
                        <input
                            required
                            className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                            value={form.codigo_postal}
                            onChange={(e) => setForm((f) => ({ ...f, codigo_postal: e.target.value }))}
                        />
                    </FormField>

                    <div className="pt-2 flex items-center gap-3">
                        <input
                            type="checkbox"
                            id="esPrincipal"
                            className="w-4 h-4 rounded border-border text-accent focus:ring-accent cursor-pointer object-contain"
                            checked={form.es_principal}
                            onChange={(e) => setForm((f) => ({ ...f, es_principal: e.target.checked }))}
                        />
                        <label htmlFor="esPrincipal" className="text-xs font-bold text-muted uppercase tracking-widest cursor-pointer select-none">
                            Definir como principal
                        </label>
                    </div>

                    <div className="pt-4 flex flex-col gap-3">
                        <LoadingButton
                            type="submit"
                            isLoading={crear.isPending || actualizar.isPending}
                            className="w-full py-4 bg-primary text-white font-bold text-sm tracking-wide rounded-xl hover:bg-primary-hover shadow-sm"
                        >
                            {editingId ? "Guardar cambios" : "Registrar Dirección"}
                        </LoadingButton>
                        
                        {editingId && (
                            <button 
                                type="button" 
                                className="w-full py-4 border border-border bg-white text-muted font-bold text-sm tracking-wide rounded-xl hover:bg-bg-secondary transition-colors"
                                onClick={() => {
                                    setEditingId(null);
                                    setForm(emptyForm);
                                }}
                            >
                                Cancelar edición
                            </button>
                        )}
                    </div>
                </form>
            </section>
        </div>

        {/* List Column -> lg:col-span-7 */}
        <div className="lg:col-span-7 order-1 lg:order-2">
            <h2 className="mb-6 md:mb-8 text-sm font-bold text-primary uppercase tracking-widest flex items-center gap-2 border-b border-border pb-4">
                <MapPinned size={18} className="text-muted" /> MIS DIRECCIONES
            </h2>

            {isLoading && (
                <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="h-32 bg-bg-secondary rounded-2xl animate-pulse border border-border"></div>
                    ))}
                </div>
            )}

            {!isLoading && data.length === 0 && (
                <EmptyState
                    titulo="No tenés direcciones guardadas"
                    descripcion="Agregá tu primera dirección desde el formulario para poder recibir tus pedidos."
                    icon={MapPin}
                />
            )}

            {!isLoading && data.length > 0 && (
                <ul className="space-y-4">
                    {data.map((d) => (
                    <li key={d.id} className={`rounded-2xl bg-white p-6 transition-all border ${editingId === d.id ? 'border-accent shadow-sm' : 'border-border shadow-sm hover:border-accent/50'}`}>
                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                    <span className="text-xs font-black text-primary uppercase tracking-widest">
                                        {d.alias ?? "Dirección"}
                                    </span>
                                    {d.es_principal && (
                                        <span className="inline-flex items-center gap-1 rounded-full bg-accent/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-accent border border-accent/20">
                                            <Star className="h-3 w-3 fill-accent text-accent" />
                                            Principal
                                        </span>
                                    )}
                                </div>
                                <p className="text-lg font-black text-primary font-outfit mb-1 break-words">
                                    {d.calle} {d.numero} {d.piso_dpto && `— Dpto: ${d.piso_dpto}`}
                                </p>
                                <p className="text-sm text-muted leading-relaxed">
                                    {d.ciudad} (CP {d.codigo_postal})
                                </p>
                            </div>
                            
                            <div className="flex sm:flex-col items-center sm:items-end gap-3 sm:gap-2 pt-2 sm:pt-0 border-t sm:border-t-0 border-border">
                                <button
                                    type="button"
                                    className="text-xs font-bold text-accent hover:text-accent-hover transition-colors uppercase tracking-widest whitespace-nowrap"
                                    onClick={() => {
                                        setEditingId(d.id);
                                        setForm({
                                            alias: d.alias ?? "",
                                            calle: d.calle,
                                            numero: d.numero,
                                            piso_dpto: d.piso_dpto ?? "",
                                            ciudad: d.ciudad,
                                            codigo_postal: d.codigo_postal,
                                            referencias: d.referencias ?? "",
                                            es_principal: d.es_principal,
                                        });
                                        // Scroll to form smoothly
                                        window.scrollTo({ top: 0, behavior: 'smooth' });
                                    }}
                                >
                                    Editar
                                </button>
                                
                                {!d.es_principal && (
                                    <button
                                        type="button"
                                        disabled={marcarPrincipal.isPending}
                                        className="text-xs font-bold text-muted hover:text-primary transition-colors uppercase tracking-widest disabled:opacity-50 whitespace-nowrap"
                                        onClick={() =>
                                            marcarPrincipal.mutate(d.id, {
                                            onSuccess: () => toast.success("Dirección principal actualizada"),
                                            onError: () => toast.error("Hubo un error al actualizar"),
                                            })
                                        }
                                    >
                                        Hacer Principal
                                    </button>
                                )}
                                
                                <button
                                    type="button"
                                    className="text-xs font-bold text-danger hover:text-danger/80 transition-colors uppercase tracking-widest whitespace-nowrap"
                                    onClick={() => setDeleteId(d.id)}
                                >
                                    Eliminar
                                </button>
                            </div>
                        </div>
                    </li>
                    ))}
                </ul>
            )}
        </div>
      </div>

      <ConfirmDialog
        open={deleteId !== null}
        title="Eliminar dirección"
        destructive
        confirmLabel={eliminar.isPending ? "Eliminando..." : "Eliminar"}
        onCancel={() => setDeleteId(null)}
        onConfirm={() => {
          if (deleteId !== null) eliminar.mutate(deleteId);
          setDeleteId(null);
        }}
      >
        <p className="text-sm font-medium text-muted">
            ¿Estás seguro que querés eliminar esta dirección? Esta acción no se puede deshacer.
        </p>
      </ConfirmDialog>
    </div>
  );
}
