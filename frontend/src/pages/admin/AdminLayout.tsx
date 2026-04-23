import { NavLink, Navigate, Outlet, Link } from "react-router-dom";

import { useAuthStore } from "@/shared/store/auth-store";
import { useAuthHydrated, useMe } from "@/features/auth";

export function AdminLayout() {
  const hydrated = useAuthHydrated();
  const token = useAuthStore((s) => s.access_token);
  const { data: me, isLoading } = useMe();

  if (!hydrated || isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm font-bold uppercase tracking-widest text-muted animate-pulse">
            Sincronizando...
        </p>
      </div>
    );
  }
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // verifico si el usuario tiene el rol ADMIN
  if (!me?.roles?.includes("ADMIN")) {
    return (
      <div className="mx-auto max-w-lg rounded-2xl border border-border bg-white p-8 text-center shadow-sm fade-in mt-12">
        <h1 className="mb-4 text-xl font-bold text-primary">Acceso Denegado</h1>
        <p className="text-sm text-muted mb-8">Se requiere autorización de nivel administrador para este sector.</p>
        <Link to="/" className="inline-block px-6 py-3 bg-primary text-white font-bold text-sm rounded-xl hover:bg-primary-hover transition-colors shadow-sm">
          Volver al Home
        </Link>
      </div>
    );
  }

  return (
    <div className="fade-in min-w-0 px-2 md:px-0">
      <header className="mb-6 md:mb-10 text-center md:text-left flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
            <h1 className="text-2xl md:text-4xl font-black text-primary font-outfit uppercase tracking-tight mb-2">
            Panel de Control
            </h1>
            <p className="text-xs font-bold uppercase tracking-widest text-muted">Gestión integral de la plataforma</p>
        </div>
        <button
          onClick={() => {
            const logout = useAuthStore.getState().logout;
            logout();
          }}
          className="flex items-center justify-center gap-2 rounded-xl border border-border bg-white px-4 py-3 text-xs font-bold uppercase tracking-widest text-danger shadow-sm hover:bg-danger/10 transition-colors"
        >
          Cerrar Sesión
        </button>
      </header>

      <nav className="mb-8 flex items-center gap-4 md:gap-8 overflow-x-auto pb-4 border-b border-border scrollbar-hide">
        {[
          { label: "Dashboard", to: "/admin" },
          { label: "Catálogo", to: "/admin/productos" },
          { label: "Categorías", to: "/admin/categorias" },
          { label: "Ingredientes", to: "/admin/ingredientes" },
          { label: "Pedidos", to: "/admin/pedidos" },
        ].map((item) => (
          <NavLink
            key={item.to}
            end={item.to === "/admin"}
            to={item.to}
            className={({ isActive }) =>
              `text-xs font-bold uppercase tracking-widest pb-3 -mb-[17px] border-b-2 transition-all whitespace-nowrap ${
                isActive 
                  ? "text-primary border-primary" 
                  : "text-muted border-transparent hover:text-primary hover:border-border"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="max-w-full min-w-0 overflow-x-auto">
        <Outlet />
      </div>
    </div>
  );
}
