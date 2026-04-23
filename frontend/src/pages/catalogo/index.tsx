import { useState, useEffect } from "react";
import axios from "axios";
import { useQuery } from "@tanstack/react-query";
import { Search, X } from "lucide-react";

import { ProductoList } from "@/features/productos/ui/ProductoList";
import { useProductos } from "@/features/productos/hooks/useProductos";
import { CatalogoSkeleton } from "@/shared/ui";
import { categoriasApi } from "@/shared/api/endpoints/categorias";

function catalogoErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const st = error.response?.status;
    const detail = error.response?.data;
    const msg =
      typeof detail === "object" && detail !== null && "detail" in detail
        ? String((detail as { detail: unknown }).detail)
        : error.message;
    return st ? `HTTP ${st}: ${msg}` : msg;
  }
  return error instanceof Error ? error.message : "Error desconocido";
}

export function CatalogoPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [categoriaId, setCategoriaId] = useState<number | "">("");

  // TODO: agregar busqueda en tiempo real con debounce
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedSearch(searchTerm), 300);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  const { data: categoriasResp } = useQuery({
    queryKey: ["categorias", "todas"],
    queryFn: () => categoriasApi.listar({ size: 100 }),
  });

  const categorias = categoriasResp?.items ?? [];

  // cargo los datos del back
  const { data, isLoading, isError, error, refetch } = useProductos({
    page: 1,
    size: 50,
    search: debouncedSearch || undefined,
    categoria_id: categoriaId !== "" ? categoriaId : undefined,
  });

  const isFiltering = debouncedSearch !== "" || categoriaId !== "";

  const clearFilters = () => {
    setSearchTerm("");
    setDebouncedSearch("");
    setCategoriaId("");
  };

  return (
    <div className="min-w-0 space-y-6 md:space-y-12 pb-16 sm:pb-20">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl md:rounded-[2.5rem] bg-slate-950 px-4 py-8 text-center sm:py-10 md:px-16 md:py-32 shadow-2xl">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black opacity-100"></div>
        <div className="relative z-10 mx-auto max-w-4xl flex flex-col md:flex-row items-center md:items-start text-left gap-6 md:gap-12">
            <div className="flex-1 text-center md:text-left">
              <span className="inline-block px-3 py-1 mb-4 md:mb-8 text-[9px] md:text-[10px] font-black tracking-[0.3em] text-slate-400 uppercase bg-white/5 rounded-lg border border-white/10 backdrop-blur-sm">
                  Exclusividad · Calidad · Tradición
              </span>
              <h1 className="text-2xl sm:text-5xl md:text-7xl font-black text-white font-outfit leading-[1.15] tracking-tighter uppercase">
                  CONCURSO GOURMET <br className="hidden md:block"/> <span className="text-slate-500">PARA PALADARES SELECTOS</span>
              </h1>
              <p className="mt-4 md:mt-8 text-[11px] md:text-xl text-slate-400 font-medium leading-relaxed max-w-2xl mx-auto md:mx-0 px-0 line-clamp-2 md:line-clamp-none">
                  Una curaduría de los ingredientes más finos y preparaciones artesanales, entregados con la distinción que su mesa merece.
              </p>
            </div>
            {/* Imagen decorativa a la derecha (Desktop) */}
            <div className="hidden md:block w-72 h-72 rounded-full border-4 border-white/5 overflow-hidden filter grayscale opacity-40 hover:opacity-100 hover:grayscale-0 transition-all duration-700">
               <div className="w-full h-full bg-cover bg-center" style={{ backgroundImage: "url('https://images.unsplash.com/photo-1544148103-0773bf10d330?q=80&w=600&auto=format&fit=crop')" }}></div>
            </div>
        </div>
      </section>

      {/* Control de barra de filtros */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
                <h2 className="text-xl md:text-3xl font-black text-slate-950 font-outfit uppercase tracking-tighter">Nuestro Catálogo</h2>
                <p className="text-slate-400 font-black text-xs md:text-sm uppercase tracking-widest mt-1">
                    {data ? `${data.total} tesoros culinarios encontrados` : "Explorá nuestras delicias"}
                </p>
            </div>
            
            {/* Filtros */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full md:w-auto overflow-x-auto pb-2 sm:pb-0">
                <div className="relative min-w-[200px] shrink-0">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Buscar delicias..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="h-11 w-full rounded-xl border border-border bg-bg-secondary pl-10 pr-4 text-sm font-medium focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <select
                  value={categoriaId}
                  onChange={(e) => setCategoriaId(e.target.value === "" ? "" : Number(e.target.value))}
                  className="h-11 min-w-[160px] shrink-0 rounded-xl border border-border bg-bg-secondary px-4 text-sm font-medium focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary appearance-none"
                >
                  <option value="">Todas las categorías</option>
                  {categorias.map((c) => (
                    <option key={c.id} value={c.id}>{c.nombre}</option>
                  ))}
                </select>
                {isFiltering && (
                  <button
                    onClick={clearFilters}
                    className="flex shrink-0 h-11 items-center gap-2 rounded-xl bg-danger/10 px-4 text-sm font-bold text-danger hover:bg-danger/20 transition-colors"
                  >
                    <X size={16} /> <span className="hidden sm:inline">Limpiar</span>
                  </button>
                )}
            </div>
        </div>
      </div>

      {isLoading ? (
        <CatalogoSkeleton />
      ) : isError ? (
        <div className="rounded-3xl border border-red-100 bg-red-50/50 p-8 text-red-900 premium-shadow">
          <h2 className="text-xl font-bold flex flex-wrap items-center gap-2 mb-2">
              Lo sentimos, hubo un problema
          </h2>
          <p className="text-sm opacity-90 break-words">{catalogoErrorMessage(error)}</p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="mt-6 w-full min-h-11 rounded-2xl bg-red-600 px-6 py-3 text-sm font-bold text-white hover:bg-red-700 transition-colors shadow-lg shadow-red-100 sm:w-auto active:scale-95"
          >
            Intentar de nuevo
          </button>
        </div>
      ) : (
        <ProductoList productos={data?.items ?? []} />
      )}
    </div>
  );
}
