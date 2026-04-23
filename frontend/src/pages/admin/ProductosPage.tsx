import { useEffect, useMemo, useState } from "react";
import { Check } from "lucide-react";

import {
  aplanarCategoriasParaSelect,
  buildCategoriaArbol,
  useActualizarProducto,
  useAdminProductoMutations,
  useCategorias,
  useIngredientesTodos,
} from "@/features/admin";
import { useProductos } from "@/features/productos/hooks/useProductos";
import { apiErrorDetail } from "@/shared/api/apiErrorDetail";
import type { ProductoListadoItemDTO } from "@/shared/api/endpoints/productos";
import { ConfirmDialog, FormField, LoadingButton } from "@/shared/ui";
import { toast } from "sonner";

function formatMoney(value: number) {
  return value.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 });
}

type EditForm = {
  nombre: string;
  precio: string;
  descripcion: string;
  categoria_id: string;
  disponible: boolean;
  stock_cantidad: string;
  ingredientes_ids: number[];
};

const EDIT_FORM_INICIAL: EditForm = {
  nombre: "",
  precio: "",
  descripcion: "",
  categoria_id: "",
  disponible: true,
  stock_cantidad: "0",
  ingredientes_ids: [],
};

export function AdminProductosPage() {
  // cargo los datos del back
  const { data, isLoading } = useProductos({ page: 1, size: 100 });
  const { data: categorias = [], isLoading: categoriasLoading } = useCategorias();
  const { data: todosIngredientes = [] } = useIngredientesTodos();
  const { crear, patch, stock, eliminar } = useAdminProductoMutations();
  const actualizarProducto = useActualizarProducto();

  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [stockDraft, setStockDraft] = useState<Record<number, string>>({});

  // ── Estado del modal de edición ──────────────────────────────────────────
  const [editProduct, setEditProduct] = useState<ProductoListadoItemDTO | null>(null);
  const [editForm, setEditForm] = useState<EditForm>(EDIT_FORM_INICIAL);

  // ── Opciones de categoría para selects ──────────────────────────────────
  const opcionesCategoria = useMemo(() => {
    const arbol = buildCategoriaArbol(categorias);
    return aplanarCategoriasParaSelect(arbol);
  }, [categorias]);

  // Mapa id → nombre para mostrar en la tabla
  const categoriaById = useMemo(() => {
    const m = new Map<number, string>();
    for (const c of categorias) m.set(c.id, c.nombre);
    return m;
  }, [categorias]);

  // ── Formulario de creación ───────────────────────────────────────────────
  const [form, setForm] = useState({
    categoria_id: "",
    nombre: "",
    precio: "",
    stock_cantidad: "0",
  });

  useEffect(() => {
    setForm((f) => {
      if (f.categoria_id !== "" || opcionesCategoria.length === 0) return f;
      return { ...f, categoria_id: String(opcionesCategoria[0].id) };
    });
  }, [opcionesCategoria]);

  const items = data?.items ?? [];

  const pendingDelete = useMemo(
    () => items.find((p) => p.id === deleteId)?.nombre ?? "",
    [deleteId, items],
  );

  // ── Helpers del modal de edición ─────────────────────────────────────────
  function abrirEditar(p: ProductoListadoItemDTO) {
    // abro el modal con los datos cargados
    setEditProduct(p);
    setEditForm({
      nombre: p.nombre,
      precio: String(Number(p.precio)),
      descripcion: p.descripcion ?? "",
      categoria_id: String(p.categoria_id),
      disponible: p.disponible,
      stock_cantidad: String(p.stock_cantidad),
      ingredientes_ids: (p.ingredientes ?? []).map((i) => i.ingrediente_id),
    });
  }

  function cerrarEditar() {
    setEditProduct(null);
    setEditForm(EDIT_FORM_INICIAL);
  }

  function toggleIngrediente(id: number) {
    setEditForm((f) => ({
      ...f,
      ingredientes_ids: f.ingredientes_ids.includes(id)
        ? f.ingredientes_ids.filter((x) => x !== id)
        : [...f.ingredientes_ids, id],
    }));
  }

  function guardarEdicion() {
    if (!editProduct) return;

    const nombre = editForm.nombre.trim();
    if (!nombre) { toast.error("El nombre es obligatorio."); return; }

    const precio = Number(editForm.precio);
    if (!Number.isFinite(precio) || precio <= 0) {
      toast.error("El precio debe ser mayor a 0.");
      return;
    }

    const categoria_id = Number(editForm.categoria_id);
    if (!Number.isFinite(categoria_id) || categoria_id < 1) {
      toast.error("Seleccioná una categoría válida.");
      return;
    }

    // Preservar cantidad existente para ingredientes que ya tenía el producto
    const cantidadesPrevias = new Map(
      (editProduct.ingredientes ?? []).map((i) => [i.ingrediente_id, Number(i.cantidad)]),
    );

    const ingredientes = editForm.ingredientes_ids.map((ingId) => ({
      ingrediente_id: ingId,
      cantidad: cantidadesPrevias.get(ingId) ?? 1,
      es_removible: true,
    }));

    actualizarProducto.mutate(
      {
        id: editProduct.id,
        data: {
          nombre,
          precio,
          descripcion: editForm.descripcion.trim() || null,
          categoria_id,
          disponible: editForm.disponible,
          ingredientes: ingredientes as unknown[],
        },
      },
      {
        onSuccess: () => {
          // esto recarga la lista despues de guardar
          const newStock = Number(editForm.stock_cantidad);
          if (
            Number.isFinite(newStock) &&
            newStock >= 0 &&
            newStock !== editProduct.stock_cantidad
          ) {
            stock.mutate({ id: editProduct.id, stock_cantidad: newStock });
          }
          toast.success("Producto actualizado.");
          cerrarEditar();
        },
        onError: (err) => {
          // si falla muestro el error en un toast
          toast.error(apiErrorDetail(err, "No se pudo actualizar el producto."));
        },
      },
    );
  }

  if (isLoading || categoriasLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm font-bold uppercase tracking-widest text-muted animate-pulse">
          Sincronizando Catálogo...
        </p>
      </div>
    );
  }

  return (
    <div className="min-w-0 space-y-8 pb-16 sm:space-y-12 sm:pb-20">

      {/* ── Formulario de creación ─────────────────────────────────────── */}
      <section className="rounded-2xl border border-border bg-white p-6 shadow-sm md:p-8">
        <h2 className="mb-6 border-b border-border pb-4 text-sm font-bold uppercase tracking-widest text-primary">
          Nuevo Producto
        </h2>
        <form
          className="grid grid-cols-1 items-end gap-4 sm:grid-cols-2 lg:grid-cols-5"
          onSubmit={(e) => {
            e.preventDefault();
            const categoria_id = Number(form.categoria_id);
            const precio = Number(form.precio);
            const stock_cantidad = Number(form.stock_cantidad);
            if (!form.nombre.trim()) {
              toast.error("Indicá el nombre del producto.");
              return;
            }
            if (!Number.isFinite(precio) || precio <= 0) {
              toast.error("El precio tiene que ser un número mayor a 0.");
              return;
            }
            const idsValidos = new Set(opcionesCategoria.map((o) => o.id));
            if (!Number.isFinite(categoria_id) || !idsValidos.has(categoria_id)) {
              toast.error("Seleccioná una categoría válida del listado.");
              return;
            }
            crear.mutate({
              categoria_id: Number.isFinite(categoria_id) && categoria_id >= 1 ? categoria_id : 1,
              nombre: form.nombre.trim(),
              precio,
              stock_cantidad: Number.isFinite(stock_cantidad) && stock_cantidad >= 0 ? stock_cantidad : 0,
              ingredientes: [],
            });
            setForm({
              categoria_id: form.categoria_id,
              nombre: "",
              precio: "",
              stock_cantidad: "0",
            });
          }}
        >
          <FormField label="Categoría" className="lg:col-span-1">
            <select
              className="mt-1 w-full bg-bg-secondary border border-border rounded-xl px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white outline-none transition-all"
              value={form.categoria_id}
              onChange={(e) => setForm((f) => ({ ...f, categoria_id: e.target.value }))}
            >
              {opcionesCategoria.length === 0 ? (
                <option value="">Sin categorías</option>
              ) : (
                opcionesCategoria.map((o) => (
                  <option key={o.id} value={String(o.id)}>
                    {o.label}
                  </option>
                ))
              )}
            </select>
          </FormField>

          <FormField label="Nombre" className="lg:col-span-1">
            <input
              className="mt-1 w-full bg-bg-secondary border border-border rounded-xl px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white outline-none transition-all"
              placeholder="Ej: Hamburguesa Simple"
              value={form.nombre}
              onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
            />
          </FormField>

          <FormField label="Precio" className="lg:col-span-1">
            <input
              type="number"
              step="0.01"
              min="0"
              className="mt-1 w-full bg-bg-secondary border border-border rounded-xl px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white outline-none transition-all"
              value={form.precio}
              onChange={(e) => setForm((f) => ({ ...f, precio: e.target.value }))}
            />
          </FormField>

          <FormField label="Stock inicial" className="lg:col-span-1">
            <input
              type="number"
              min="0"
              className="mt-1 w-full bg-bg-secondary border border-border rounded-xl px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white outline-none transition-all"
              value={form.stock_cantidad}
              onChange={(e) => setForm((f) => ({ ...f, stock_cantidad: e.target.value }))}
            />
          </FormField>

          <div className="lg:col-span-1">
            <LoadingButton
              type="submit"
              isLoading={crear.isPending}
              className="w-full h-[46px] bg-primary text-white font-bold text-sm rounded-xl hover:bg-primary-hover shadow-sm transition-all"
            >
              Confirmar Alta
            </LoadingButton>
          </div>
        </form>
      </section>

      {/* ── Tabla de productos ─────────────────────────────────────────── */}
      <div className="overflow-hidden rounded-2xl border border-border bg-white shadow-sm">
        <div className="overflow-x-auto overscroll-x-contain">
          <table className="w-full min-w-[820px] border-collapse text-left">
            <thead className="bg-bg-secondary border-b border-border">
              <tr>
                <th className="px-4 py-4 text-xs font-bold uppercase tracking-widest text-muted">ID</th>
                {/* TODO: mostrar imagen del producto en la tabla admin */}
                <th className="px-4 py-4 text-xs font-bold uppercase tracking-widest text-muted">Nombre</th>
                <th className="px-4 py-4 text-xs font-bold uppercase tracking-widest text-muted">Categoría</th>
                <th className="px-4 py-4 text-xs font-bold uppercase tracking-widest text-muted">Precio</th>
                <th className="px-4 py-4 text-xs font-bold uppercase tracking-widest text-muted">Disponibilidad</th>
                <th className="px-4 py-4 text-xs font-bold uppercase tracking-widest text-muted">Stock</th>
                <th className="px-4 py-4 text-right text-xs font-bold uppercase tracking-widest text-muted">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {items.map((p) => (
                <tr key={p.id} className="hover:bg-bg-secondary/50 transition-colors">
                  <td className="px-4 py-4 font-outfit text-sm font-black text-primary">#{p.id}</td>
                  <td className="px-4 py-4">
                    <span className="text-sm font-bold text-primary">{p.nombre}</span>
                  </td>
                  <td className="px-4 py-4">
                    <span className="text-sm font-medium text-muted">
                      {categoriaById.get(p.categoria_id) ?? "—"}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-sm font-bold text-primary whitespace-nowrap">
                    {formatMoney(typeof p.precio === "number" ? p.precio : Number(p.precio))}
                  </td>
                  <td className="px-4 py-4">
                    <button
                      type="button"
                      className={`px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest border transition-all ${
                        p.disponible
                          ? "bg-accent/10 text-accent border-accent/20"
                          : "bg-muted/10 text-muted border-muted/20"
                      }`}
                      onClick={() => patch.mutate({ id: p.id, body: { disponible: !p.disponible } })}
                    >
                      {p.disponible ? "Activo" : "Pausado"}
                    </button>
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      <input
                        className="w-20 bg-white border border-border rounded-lg px-3 py-2 text-sm font-bold text-primary focus:border-accent outline-none transition-all shadow-sm"
                        value={stockDraft[p.id] ?? String(p.stock_cantidad)}
                        onChange={(e) => setStockDraft((d) => ({ ...d, [p.id]: e.target.value }))}
                      />
                      {stockDraft[p.id] !== undefined && stockDraft[p.id] !== String(p.stock_cantidad) && (
                        <button
                          type="button"
                          className="p-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors shadow-sm"
                          onClick={() => {
                            const n = Number(stockDraft[p.id] ?? p.stock_cantidad);
                            if (Number.isFinite(n) && n >= 0) stock.mutate({ id: p.id, stock_cantidad: n });
                          }}
                        >
                          <Check size={16} />
                        </button>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4 text-right">
                    <div className="flex justify-end gap-4">
                      <button
                        type="button"
                        className="text-xs font-bold uppercase tracking-widest text-muted hover:text-primary transition-colors"
                        onClick={() => abrirEditar(p)}
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        className="text-xs font-bold text-danger hover:text-danger/80 transition-colors uppercase tracking-widest"
                        onClick={() => setDeleteId(p.id)}
                      >
                        Eliminar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Modal de edición ──────────────────────────────────────────────── */}
      {editProduct !== null && (
        <div
          className="fixed inset-0 z-[60] flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4 fade-in"
          role="dialog"
          aria-modal="true"
        >
          <div className="max-h-[min(92dvh,100vh)] w-full max-w-lg overflow-y-auto overscroll-contain rounded-t-2xl border border-border bg-white p-6 shadow-xl sm:rounded-2xl md:p-8 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
            <h3 className="text-sm font-bold uppercase tracking-widest text-primary border-b border-border pb-4 mb-6">
              Editar producto <span className="font-outfit font-black">#{editProduct.id}</span>
            </h3>

            <div className="space-y-4">
              {/* Nombre */}
              <FormField label="Nombre">
                <input
                  className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                  maxLength={200}
                  value={editForm.nombre}
                  onChange={(e) => setEditForm((f) => ({ ...f, nombre: e.target.value }))}
                />
              </FormField>

              {/* Precio */}
              <FormField label="Precio ($)">
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                  value={editForm.precio}
                  onChange={(e) => setEditForm((f) => ({ ...f, precio: e.target.value }))}
                />
              </FormField>

              {/* Descripción */}
              <FormField label="Descripción (opcional)">
                <textarea
                  className="mt-1 min-h-[80px] w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all resize-y"
                  maxLength={10000}
                  rows={3}
                  value={editForm.descripcion}
                  onChange={(e) => setEditForm((f) => ({ ...f, descripcion: e.target.value }))}
                />
              </FormField>

              {/* Categoría */}
              <FormField label="Categoría">
                <select
                  className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                  value={editForm.categoria_id}
                  onChange={(e) => setEditForm((f) => ({ ...f, categoria_id: e.target.value }))}
                >
                  {opcionesCategoria.map((o) => (
                    <option key={o.id} value={String(o.id)}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </FormField>

              {/* Stock */}
              <FormField label="Stock">
                <input
                  type="number"
                  min="0"
                  className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                  value={editForm.stock_cantidad}
                  onChange={(e) => setEditForm((f) => ({ ...f, stock_cantidad: e.target.value }))}
                />
              </FormField>

              {/* Disponible */}
              <div className="pt-1">
                <label className="flex cursor-pointer items-center gap-3 text-xs font-bold uppercase tracking-widest text-muted hover:text-primary transition-colors max-w-fit">
                  <input
                    type="checkbox"
                    className="h-5 w-5 rounded-md border-border text-accent focus:ring-accent transition-colors"
                    checked={editForm.disponible}
                    onChange={(e) => setEditForm((f) => ({ ...f, disponible: e.target.checked }))}
                  />
                  Disponible para la venta
                </label>
              </div>

              {/* Ingredientes */}
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-muted mb-3">
                  Ingredientes
                </p>
                {todosIngredientes.length === 0 ? (
                  <p className="text-sm font-medium text-muted italic">No hay ingredientes cargados.</p>
                ) : (
                  <div className="max-h-44 overflow-y-auto overscroll-contain rounded-xl border border-border bg-bg-secondary p-3 space-y-2">
                    {[...todosIngredientes]
                      .sort((a, b) => a.nombre.localeCompare(b.nombre, "es"))
                      .map((ing) => (
                        <label
                          key={ing.id}
                          className="flex cursor-pointer items-center gap-3 rounded-lg px-2 py-1.5 hover:bg-white transition-colors"
                        >
                          <input
                            type="checkbox"
                            className="h-4 w-4 shrink-0 rounded border-border text-accent focus:ring-accent transition-colors"
                            checked={editForm.ingredientes_ids.includes(ing.id)}
                            onChange={() => toggleIngrediente(ing.id)}
                          />
                          <span className="text-sm font-bold text-primary flex-1 leading-tight">
                            {ing.nombre}
                          </span>
                          {ing.es_alergeno && (
                            <span className="shrink-0 rounded-full border border-danger/20 bg-danger/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest text-danger">
                              Alérgeno
                            </span>
                          )}
                        </label>
                      ))}
                  </div>
                )}
              </div>
            </div>

            {/* Botones */}
            <div className="mt-8 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={cerrarEditar}
                className="w-full rounded-xl border border-border px-4 py-3 text-sm font-bold text-muted hover:bg-bg-secondary transition-colors sm:w-auto"
              >
                Cancelar
              </button>
              <LoadingButton
                type="button"
                onClick={guardarEdicion}
                isLoading={actualizarProducto.isPending}
                className="w-full rounded-xl bg-primary px-6 py-3 text-sm font-bold text-white hover:bg-primary-hover shadow-sm sm:w-auto"
              >
                Guardar cambios
              </LoadingButton>
            </div>
          </div>
        </div>
      )}

      {/* ── Confirm delete ────────────────────────────────────────────────── */}
      <ConfirmDialog
        open={deleteId !== null}
        title="Eliminar Producto"
        destructive
        confirmLabel={eliminar.isPending ? "Eliminando..." : "Eliminar"}
        onCancel={() => setDeleteId(null)}
        onConfirm={() => {
          if (deleteId !== null) eliminar.mutate(deleteId);
          setDeleteId(null);
        }}
      >
        <p className="text-sm font-medium text-muted">
          ¿Confirmás que querés eliminar el producto <strong>{pendingDelete}</strong> del catálogo? Esta acción no se puede deshacer.
        </p>
      </ConfirmDialog>
    </div>
  );
}
