import type { ProductoListadoItemDTO } from "@/shared/api/endpoints/productos";

import { ProductoCard } from "./ProductoCard";

type Props = {
  productos: ProductoListadoItemDTO[];
};

export function ProductoList({ productos }: Props) {
  if (productos.length === 0) {
    return <p className="text-slate-600">No hay productos para mostrar.</p>;
  }

  return (
    <div className="grid min-w-0 grid-cols-2 gap-3 sm:grid-cols-2 md:gap-8 lg:grid-cols-3 xl:grid-cols-4">
      {productos.map((p) => (
        <ProductoCard key={p.id} producto={p} />
      ))}
    </div>
  );
}
