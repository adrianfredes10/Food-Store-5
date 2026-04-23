import { createBrowserRouter, Link, NavLink, Outlet, useLocation } from "react-router-dom";

import { useMe } from "@/features/auth";
import { AuthLoginPage } from "@/pages/auth";
import { AdminLayout } from "@/pages/admin/AdminLayout";
import { AdminDashboardPage } from "@/pages/admin/DashboardPage";
import { AdminPedidoDetallePage } from "@/pages/admin/PedidoDetallePage";
import { AdminPedidosPage } from "@/pages/admin/PedidosPage";
import { AdminCategoriasPage } from "@/pages/admin/CategoriasPage";
import { AdminIngredientesPage } from "@/pages/admin/IngredientesPage";
import { AdminProductosPage } from "@/pages/admin/ProductosPage";
import { CarritoPage } from "@/pages/carrito";
import { CatalogoPage } from "@/pages/catalogo";
import { CheckoutPage } from "@/pages/checkout";
import { GuiaPage } from "@/pages/guia";
import { DireccionesPage } from "@/pages/direcciones";
import { MisPedidosPage } from "@/pages/mis-pedidos";
import { PedidoPage } from "@/pages/pedido";
import { useAuthStore } from "@/shared/store/auth-store";
import { useCartStore } from "@/shared/store/cart-store";

import { ShoppingBag, User, Menu, X } from "lucide-react";
import { useState, useEffect } from "react";

function MainNav() {
  const location = useLocation();
  const token = useAuthStore((s) => s.access_token);
  const logout = useAuthStore((s) => s.logout);
  const { data: me } = useMe();
  const isAdmin = me?.roles?.includes("ADMIN");
  const isClient = token && !isAdmin;
  const [isOpen, setIsOpen] = useState(false);
  const cartItems = useCartStore((s) => s.items);
  const totalItems = cartItems.reduce((acc, item) => acc + item.cantidad, 0);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => { document.body.style.overflow = "unset"; };
  }, [isOpen]);

  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  return (
    <nav className="mx-auto flex flex-row items-center justify-between px-4 sm:px-6 h-14 lg:h-[72px] max-w-7xl">
      {/* Left: Logo */}
      <Link to="/" className="flex items-center gap-2 group shrink-0 w-auto lg:w-48">
        <div className="bg-primary p-2 rounded-lg text-white transition-all shadow-md group-hover:scale-105 active:scale-95 shrink-0">
          <ShoppingBag size={18} strokeWidth={2.5} />
        </div>
        <span className="truncate text-lg sm:text-xl font-black tracking-tighter text-primary font-outfit uppercase">
          FOOD<span className="text-muted">STORE</span>
        </span>
      </Link>

      {/* Center: Desktop Links (>1024px) */}
      <div className="hidden lg:flex flex-1 items-center justify-center gap-8 text-sm font-semibold text-muted">
        <NavLink to="/" className={({ isActive }) => `hover:text-primary transition-colors ${isActive ? "text-primary border-b-2 border-primary" : ""}`}>Catálogo</NavLink>
        <NavLink to="/guia" className={({ isActive }) => `hover:text-primary transition-colors ${isActive ? "text-primary border-b-2 border-primary" : ""}`}>Guía</NavLink>
        {isClient && <NavLink to="/mis-pedidos" className={({ isActive }) => `hover:text-primary transition-colors ${isActive ? "text-primary border-b-2 border-primary" : ""}`}>Mis Pedidos</NavLink>}
        {isClient && <NavLink to="/direcciones" className={({ isActive }) => `hover:text-primary transition-colors ${isActive ? "text-primary border-b-2 border-primary" : ""}`}>Direcciones</NavLink>}
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2 sm:gap-4 shrink-0 lg:w-48 lg:justify-end">
        {isAdmin && (
          <Link to="/admin" className="hidden lg:flex items-center px-3 py-1.5 text-xs font-bold text-white bg-warning hover:bg-warning/90 rounded-lg transition-colors shadow-sm">
            Panel Admin
          </Link>
        )}
        
        {!isAdmin && (
          <Link to="/carrito" className="relative p-2 text-primary hover:bg-bg-secondary rounded-xl transition-colors active:scale-95">
            <ShoppingBag size={22} strokeWidth={2.2} />
            {totalItems > 0 && (
              <span key={totalItems} className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-danger text-[10px] font-bold text-white ring-2 ring-white animate-in zoom-in duration-300">
                {totalItems}
              </span>
            )}
          </Link>
        )}
        
        <Link to={isClient ? "/direcciones" : (isAdmin ? "/admin" : "/login")} className="hidden lg:flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg bg-primary text-white hover:bg-primary-hover transition-colors active:scale-95 shadow-sm">
          <User size={16} strokeWidth={2.5} />
          <span className="max-w-[100px] truncate">{token && me ? me.nombre.split(' ')[0] : "Ingresar"}</span>
        </Link>

        {token && (
          <button 
            type="button" 
            title="Cerrar sesión"
            onClick={() => logout()} 
            className="hidden lg:flex items-center p-2 text-muted hover:bg-danger/10 hover:text-danger rounded-xl transition-colors active:scale-95"
          >
             <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-log-out"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
          </button>
        )}

        {/* Mobile/Tablet Hamburger Menu */}
        <button onClick={() => setIsOpen(!isOpen)} className="p-2 -mr-2 text-primary lg:hidden transition-transform active:scale-90" aria-label="Menu">
          {isOpen ? <X size={24} strokeWidth={2.5} /> : <Menu size={24} strokeWidth={2.5} />}
        </button>
      </div>

      {/* Mobile/Tablet Menu Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-[100] bg-slate-950 text-white transition-all fade-in lg:hidden h-screen overflow-hidden flex flex-col">
          <header className="flex items-center justify-between px-4 h-14 border-b border-white/10">
            <div className="flex items-center gap-2">
              <span className="text-xl font-black tracking-tighter font-outfit uppercase">
                FOOD<span className="text-slate-500">STORE</span>
              </span>
            </div>
            <button onClick={() => setIsOpen(false)} className="p-2 transition-transform active:scale-90">
              <X size={24} strokeWidth={2.5} />
            </button>
          </header>

          <div className="flex-1 flex flex-col p-6 overflow-y-auto">
            {token && me && (
              <div className="mb-8 border-b border-white/10 pb-6">
                <p className="text-sm text-slate-400">Hola,</p>
                <p className="text-2xl font-bold">{me.nombre}</p>
              </div>
            )}
            
            <div className="flex flex-col gap-6">
              <Link className="text-[24px] font-bold transition-colors hover:text-accent" to="/" onClick={() => setIsOpen(false)}>Catálogo</Link>
              <Link className="text-[24px] font-bold transition-colors hover:text-accent" to="/guia" onClick={() => setIsOpen(false)}>Guía</Link>
              {isClient && <Link className="text-[24px] font-bold transition-colors hover:text-accent" to="/direcciones" onClick={() => setIsOpen(false)}>Direcciones</Link>}
              {isClient && <Link className="text-[24px] font-bold transition-colors hover:text-accent" to="/mis-pedidos" onClick={() => setIsOpen(false)}>Mis pedidos</Link>}
              {isAdmin && <Link className="text-[24px] font-bold text-warning transition-colors hover:text-warning/80" to="/admin" onClick={() => setIsOpen(false)}>Panel Administrador</Link>}
            </div>

            <div className="mt-auto pt-8">
              {token ? (
                <button onClick={() => { logout(); setIsOpen(false); }} className="w-full py-4 rounded-xl bg-white/10 font-bold text-lg hover:bg-white/20 transition-colors active:scale-95">
                  Cerrar sesión
                </button>
              ) : (
                <Link to="/login" onClick={() => setIsOpen(false)} className="block w-full text-center py-4 rounded-xl bg-accent text-white font-bold text-lg hover:bg-accent-hover transition-colors active:scale-95">
                  Iniciar sesión
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}

function AppLayout() {
  return (
    <div className="min-h-screen flex flex-col fade-in overflow-x-hidden">
      <header className="sticky top-0 z-50 border-b border-slate-100 bg-white/95 shadow-sm">
        <MainNav />
      </header>
      <main className="mx-auto w-full min-w-0 max-w-6xl flex-1 px-3 sm:px-4 md:px-6 py-2 sm:py-4 md:py-12">
        <Outlet />
      </main>
      <footer className="bg-slate-950 text-white py-10 md:py-20 pb-[max(2.5rem,env(safe-area-inset-bottom))]">
        <div className="mx-auto max-w-6xl px-4 md:px-6 grid grid-cols-1 md:grid-cols-4 gap-10 md:gap-16">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4 md:mb-8 text-center md:text-left justify-center md:justify-start">
              <span className="text-lg md:text-2xl font-black tracking-tighter text-white font-outfit">
                FOOD<span className="text-slate-500">STORE</span>
              </span>
            </div>
            <p className="text-slate-400 leading-relaxed max-w-sm font-medium text-[10px] md:text-sm text-center md:text-left mx-auto md:mx-0">
              Experiencias gastronómicas de alta gama entregadas con precisión. 
              Seleccionamos solo lo mejor para los paladares más exigentes.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-1 gap-6 md:col-span-2 md:flex md:justify-end md:gap-16">
            <div className="text-center md:text-left">
              <h4 className="text-[9px] md:text-xs font-black uppercase tracking-widest text-slate-500 mb-4 md:mb-8 font-outfit text-white">Navegación</h4>
              <ul className="space-y-2 md:space-y-4 text-xs md:text-sm text-slate-400 font-medium">
                <li><Link to="/" className="hover:text-white transition-colors">Menú</Link></li>
                <li><Link to="/guia" className="hover:text-white transition-colors">Privacidad</Link></li>
                <li><Link to="/carrito" className="hover:text-white transition-colors">Términos</Link></li>
              </ul>
            </div>
            <div className="text-center md:text-left">
              <h4 className="text-[9px] md:text-xs font-black uppercase tracking-widest text-slate-500 mb-4 md:mb-8 font-outfit text-white">Contacto</h4>
              <div className="space-y-2 md:space-y-4 text-xs md:text-sm text-slate-400 font-medium break-words">
                <p>atencion@foodstore.com</p>
                <p>+54 11 4930-1022</p>
              </div>
            </div>
          </div>
        </div>
        <div className="mx-auto max-w-6xl px-4 md:px-6 mt-10 md:mt-20 pt-6 md:pt-8 border-t border-white/5 text-center text-[7px] md:text-[10px] text-slate-600 font-black uppercase tracking-[0.2em]">
          © {new Date().getFullYear()} FoodStore HQ. All rights reserved. Premium Service.
        </div>
      </footer>
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <CatalogoPage /> },
      { path: "guia", element: <GuiaPage /> },
      { path: "carrito", element: <CarritoPage /> },
      { path: "checkout", element: <CheckoutPage /> },
      { path: "direcciones", element: <DireccionesPage /> },
      { path: "mis-pedidos", element: <MisPedidosPage /> },
      { path: "pedido/:id", element: <PedidoPage /> },
      { path: "login", element: <AuthLoginPage /> },
      {
        path: "admin",
        element: <AdminLayout />,
        children: [
          { index: true, element: <AdminDashboardPage /> },
          { path: "productos", element: <AdminProductosPage /> },
          { path: "categorias", element: <AdminCategoriasPage /> },
          { path: "ingredientes", element: <AdminIngredientesPage /> },
          { path: "pedidos", element: <AdminPedidosPage /> },
          { path: "pedidos/:id", element: <AdminPedidoDetallePage /> },
        ],
      },
    ],
  },
]);
