export { useAdminDashboard } from "./hooks/useAdminDashboard";
export {
  aplanarCategoriasParaSelect,
  buildCategoriaArbol,
  useActualizarCategoria,
  useCategorias,
  useCrearCategoria,
  useEliminarCategoria,
  type CategoriaNodo,
} from "./hooks/useAdminCategorias";
export {
  useActualizarIngrediente,
  useCrearIngrediente,
  useEliminarIngrediente,
  useIngredientes,
  useIngredientesDeProducto,
  useIngredientesTodos,
} from "./hooks/useAdminIngredientes";
export { useAdminPedidoDetalle, useAdminPedidoTransicion, useAdminPedidosList } from "./hooks/useAdminPedidos";
export { useActualizarProducto, useAdminProductoMutations } from "./hooks/useAdminProductos";
