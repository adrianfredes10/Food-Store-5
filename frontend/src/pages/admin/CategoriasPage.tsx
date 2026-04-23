import { useMemo, useState } from "react";

import {
  useActualizarCategoria,
  useCategorias,
  useCrearCategoria,
  useEliminarCategoria,
} from "@/features/admin";
import { apiErrorDetail } from "@/shared/api/apiErrorDetail";
import type { CategoriaRead } from "@/shared/api/endpoints/categorias";
import { ConfirmDialog, FormField, LoadingButton } from "@/shared/ui";
import { toast } from "sonner";

type ModalMode = "closed" | "create" | "edit";

export function AdminCategoriasPage() {
  // cargo las categorias del back
  const { data: categorias = [], isLoading } = useCategorias();
  const crear = useCrearCategoria();
  const actualizar = useActualizarCategoria();
  const eliminar = useEliminarCategoria();

  const [modalMode, setModalMode] = useState<ModalMode>("closed");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({
    nombre: "",
    parent_id: "" as string,
    descripcion: "",
    orden: "0",
  });

  const [deleteTarget, setDeleteTarget] = useState<CategoriaRead | null>(null);

  const porId = useMemo(() => {
    const m = new Map<number, CategoriaRead>();
    for (const c of categorias) m.set(c.id, c);
    return m;
  }, [categorias]);

  const filasOrdenadas = useMemo(() => {
    return [...categorias].sort((a, b) => a.orden - b.orden || a.nombre.localeCompare(b.nombre, "es"));
  }, [categorias]);

  const opcionesPadre = useMemo(() => {
    return categorias
      .filter((c) => c.activo && c.id !== editingId)
      .sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
  }, [categorias, editingId]);

  function abrirCrear() {
    setEditingId(null);
    setForm({ nombre: "", parent_id: "", descripcion: "", orden: "0" });
    setModalMode("create");
  }

  function abrirEditar(c: CategoriaRead) {
    // abro el modal con los datos cargados
    setEditingId(c.id);
    setForm({
      nombre: c.nombre,
      parent_id: c.parent_id === null ? "" : String(c.parent_id),
      descripcion: c.descripcion ?? "",
      orden: String(c.orden),
    });
    setModalMode("edit");
  }

  function cerrarModal() {
    setModalMode("closed");
    setEditingId(null);
  }

  function guardar() {
    const nombre = form.nombre.trim();
    if (!nombre) {
      toast.error("El nombre es obligatorio.");
      return;
    }
    if (nombre.length > 120) {
      toast.error("El nombre no puede superar 120 caracteres.");
      return;
    }
    const ordenNum = Number(form.orden);
    const orden = Number.isFinite(ordenNum) && ordenNum >= 0 ? ordenNum : 0;
    const parent_id = form.parent_id === "" ? null : Number(form.parent_id);
    if (form.parent_id !== "" && (!Number.isFinite(parent_id) || parent_id! < 1)) {
      toast.error("Seleccioná una categoría padre válida o dejá raíz.");
      return;
    }

    const descripcion = form.descripcion.trim() ? form.descripcion.trim() : null;

    if (modalMode === "create") {
      crear.mutate(
        {
          nombre,
          parent_id,
          descripcion,
          orden,
          activo: true,
        },
        {
          onSuccess: () => {
            toast.success("Categoría creada.");
            cerrarModal();
          },
          onError: (err) => toast.error(apiErrorDetail(err, "No se pudo crear la categoría.")),
        },
      );
      return;
    }

    if (modalMode === "edit" && editingId !== null) {
      actualizar.mutate(
        {
          id: editingId,
          data: {
            nombre,
            parent_id,
            descripcion,
            orden,
          },
        },
        {
          onSuccess: () => {
            // esto recarga la lista despues de guardar
            toast.success("Categoría actualizada.");
            cerrarModal();
          },
          onError: (err) => {
            // si falla muestro el error en un toast
            toast.error(apiErrorDetail(err, "No se pudo actualizar la categoría."));
          },
        },
      );
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm font-bold uppercase tracking-widest text-muted animate-pulse">
          Sincronizando categorías...
        </p>
      </div>
    );
  }

  const estaVacio = filasOrdenadas.length === 0;

  return (
    <div className="min-w-0 space-y-8 pb-16 sm:space-y-8 sm:pb-20">
      <section className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-2xl border border-border bg-white p-6 shadow-sm md:p-8">
        <h2 className="text-sm font-bold uppercase tracking-widest text-primary">
          Categorías
        </h2>
        <button
          type="button"
          onClick={abrirCrear}
          className="rounded-xl shrink-0 bg-primary px-6 py-3 text-sm font-bold text-white hover:bg-primary-hover shadow-sm transition-all"
        >
          Nueva categoría
        </button>
      </section>

      <div className="overflow-hidden rounded-2xl border border-border bg-white shadow-sm">
        <div className="overflow-x-auto overscroll-x-contain">
          <table className="w-full min-w-[720px] border-collapse text-left">
            <thead className="bg-bg-secondary border-b border-border">
              <tr>
                <th className="px-4 py-4 text-xs font-bold uppercase tracking-widest text-muted">
                  Nombre
                </th>
                <th className="px-4 py-4 text-xs font-bold uppercase tracking-widest text-muted">
                  Padre
                </th>
                <th className="px-4 py-4 text-xs font-bold uppercase tracking-widest text-muted">
                  Orden
                </th>
                <th className="px-4 py-4 text-xs font-bold uppercase tracking-widest text-muted">
                  Estado
                </th>
                <th className="px-4 py-4 text-right text-xs font-bold uppercase tracking-widest text-muted">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {estaVacio ? (
                <tr>
                  <td colSpan={5} className="px-6 py-16 text-center">
                    <p className="text-xs font-bold uppercase tracking-widest text-muted">
                      No hay categorías todavía. Creá la primera con "Nueva categoría".
                    </p>
                  </td>
                </tr>
              ) : (
                filasOrdenadas.map((c) => {
                  const padreNombre =
                    c.parent_id === null ? "—" : (porId.get(c.parent_id)?.nombre ?? "—");
                  return (
                    <tr key={c.id} className="hover:bg-bg-secondary/50 transition-colors">
                      <td className="px-4 py-4">
                        <span className="text-sm font-bold text-primary">
                          {c.nombre}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-sm font-bold text-muted">
                        {padreNombre}
                      </td>
                      <td className="px-4 py-4 font-outfit text-sm font-black text-primary">
                        {c.orden}
                      </td>
                      <td className="px-4 py-4">
                        <span
                          className={`inline-block rounded-full border px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest ${
                            c.activo
                              ? "border-accent/20 bg-accent/10 text-accent"
                              : "border-muted/20 bg-muted/10 text-muted"
                          }`}
                        >
                          {c.activo ? "Activo" : "Inactivo"}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-right">
                        <div className="flex flex-wrap justify-end gap-3">
                          <button
                            type="button"
                            className="text-xs font-bold uppercase tracking-widest text-muted hover:text-primary transition-colors"
                            onClick={() => abrirEditar(c)}
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            className="text-xs font-bold uppercase tracking-widest text-danger hover:text-danger/80 transition-colors"
                            onClick={() => setDeleteTarget(c)}
                          >
                            Eliminar
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {modalMode !== "closed" && (
        <div
          className="fixed inset-0 z-[60] flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4 fade-in"
          role="dialog"
          aria-modal="true"
        >
          <div className="max-h-[min(90dvh,100vh)] w-full max-w-lg overflow-y-auto overscroll-contain rounded-t-2xl border border-border bg-white p-6 shadow-xl sm:rounded-2xl md:p-8 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
            <h3 className="text-sm font-bold uppercase tracking-widest text-primary border-b border-border pb-4 mb-6">
              {modalMode === "create" ? "Nueva categoría" : "Editar categoría"}
            </h3>
            <div className="space-y-4">
                <FormField label="Nombre">
                    <input
                        className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                        maxLength={120}
                        value={form.nombre}
                        onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
                        required
                    />
                </FormField>
                <FormField label="Categoría padre">
                    <select
                        className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                        value={form.parent_id}
                        onChange={(e) => setForm((f) => ({ ...f, parent_id: e.target.value }))}
                    >
                    <option value="">Sin categoría padre (raíz)</option>
                    {opcionesPadre.map((c) => (
                        <option key={c.id} value={String(c.id)}>
                        {c.nombre}
                        </option>
                    ))}
                    </select>
                </FormField>
                <FormField label="Descripción">
                    <textarea
                        className="mt-1 min-h-[88px] w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all resize-y"
                        value={form.descripcion}
                        onChange={(e) => setForm((f) => ({ ...f, descripcion: e.target.value }))}
                        rows={3}
                    />
                </FormField>
                <FormField label="Orden">
                    <input
                        type="number"
                        min={0}
                        className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                        value={form.orden}
                        onChange={(e) => setForm((f) => ({ ...f, orden: e.target.value }))}
                    />
                </FormField>
            </div>
            <div className="mt-8 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={cerrarModal}
                className="w-full rounded-xl border border-border px-4 py-3 text-sm font-bold text-muted hover:bg-bg-secondary transition-colors sm:w-auto"
              >
                Cancelar
              </button>
              <LoadingButton
                type="button"
                onClick={guardar}
                isLoading={crear.isPending || actualizar.isPending}
                className="w-full rounded-xl bg-primary px-6 py-3 text-sm font-bold text-white hover:bg-primary-hover shadow-sm sm:w-auto"
              >
                Guardar
              </LoadingButton>
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={deleteTarget !== null}
        title="Eliminar categoría"
        destructive
        confirmLabel={eliminar.isPending ? "Eliminando..." : "Eliminar"}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => {
          if (deleteTarget === null) return;
          const id = deleteTarget.id;
          eliminar.mutate(id, {
            onSuccess: () => {
              toast.success("Categoría eliminada.");
              setDeleteTarget(null);
            },
            onError: (err) => {
              toast.error(apiErrorDetail(err, "No se pudo eliminar la categoría."));
              setDeleteTarget(null);
            },
          });
        }}
      >
        <p className="text-sm font-medium text-muted">
          ¿Eliminar la categoría &apos;<span className="font-bold">{deleteTarget?.nombre}</span>&apos;? Esta acción no se puede deshacer.
        </p>
      </ConfirmDialog>
    </div>
  );
}
