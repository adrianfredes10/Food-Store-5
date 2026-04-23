import { useQuery } from "@tanstack/react-query";

import {
  type ProductosQueryParams,
  getProductos,
} from "@/shared/api/endpoints/productos";

export function useProductos(params: ProductosQueryParams = {}) {
  return useQuery({
    queryKey: ["productos", params] as const,
    queryFn: () => getProductos(params),
  });
}
