import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useAdminDashboard } from "@/features/admin";

function toNum(v: string | number) {
  return typeof v === "number" ? v : Number.parseFloat(String(v));
}

export function AdminDashboardPage() {
  // cargo las metricas del back
  const { data, isLoading, isError } = useAdminDashboard();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm font-bold uppercase tracking-widest text-muted animate-pulse">
            Cargando métricas...
        </p>
      </div>
    );
  }
  
  if (isError || !data) {
    return (
      <div className="p-8 rounded-2xl bg-danger/5 border border-danger/20 text-center">
        <p className="text-sm font-bold text-danger uppercase tracking-widest">
            Falla en la recuperación de métricas de rendimiento.
        </p>
      </div>
    );
  }

  // armo los datos para los graficos
  const barData = Object.entries(data.pedidos_por_estado).map(([estado, cantidad]) => ({
    estado,
    cantidad,
  }));

  const lineData = data.ventas_por_dia.map((v) => ({
    fecha: v.fecha,
    total: toNum(v.total),
  }));

  const totalIngresosNum = toNum(data.ingresos_totales);

  return (
    <div className="min-w-0 space-y-6 pb-10 md:space-y-8 md:pb-20">
      {/* Metrics Grid */}
      <div className="grid grid-cols-1 gap-4 min-w-0 sm:grid-cols-2 md:grid-cols-3 md:gap-6">
        <div className="flex h-full min-w-0 flex-col justify-between rounded-2xl border border-border bg-white p-6 shadow-sm">
          <span className="text-xs font-bold text-muted uppercase tracking-widest mb-6">Volumen Pedidos</span>
          <p className="text-3xl md:text-4xl font-black text-primary font-outfit tracking-tighter">{data.total_pedidos}</p>
        </div>
        
        <div className="flex h-full min-w-0 flex-col justify-between rounded-2xl bg-primary p-6 text-white shadow-sm">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-widest mb-6">Ingresos</span>
          <div>
            <p className="break-words text-2xl font-black font-outfit tracking-tighter mb-1 sm:text-3xl md:text-4xl">
                {totalIngresosNum.toLocaleString("es-AR", {
                style: "currency",
                currency: "ARS",
                maximumFractionDigits: 0
                })}
            </p>
            <p className="text-[10px] font-bold text-slate-400">Total en órdenes finalizadas</p>
          </div>
        </div>

        <div className="flex h-full min-w-0 flex-col justify-between rounded-2xl border border-border bg-white p-6 shadow-sm sm:col-span-2 md:col-span-1">
          <span className="text-xs font-bold text-muted uppercase tracking-widest mb-6">Estado de Red</span>
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
            <p className="text-sm font-bold text-primary">Sistemas en línea</p>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 gap-6 min-w-0 lg:grid-cols-2">
        <section className="min-w-0 rounded-2xl border border-border bg-white p-6 shadow-sm md:p-8">
          <h2 className="mb-6 border-b border-border pb-4 font-outfit text-sm font-black uppercase tracking-widest text-primary">
            Distribución de Estados
          </h2>
          <div className="mt-2 h-48 min-w-0 md:mt-4 md:h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
                <XAxis 
                    dataKey="estado" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fontSize: 10, fontWeight: 700, fill: 'var(--color-muted)' }} 
                    dy={5}
                />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: 'var(--color-muted)' }} />
                <Tooltip 
                    contentStyle={{ borderRadius: '0.75rem', border: '1px solid var(--color-border)', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', fontSize: '11px', fontWeight: 'bold' }}
                />
                <Bar dataKey="cantidad" fill="var(--color-primary)" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="min-w-0 rounded-2xl border border-border bg-white p-6 shadow-sm md:p-8">
          <h2 className="mb-6 border-b border-border pb-4 font-outfit text-sm font-black uppercase tracking-widest text-primary">
            Evolución de Ventas
          </h2>
          <div className="mt-2 h-48 min-w-0 md:mt-4 md:h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={lineData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
                <XAxis 
                    dataKey="fecha" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fontSize: 10, fontWeight: 700, fill: 'var(--color-muted)' }} 
                    dy={5}
                />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: 'var(--color-muted)' }} />
                <Tooltip 
                    contentStyle={{ borderRadius: '0.75rem', border: '1px solid var(--color-border)', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', fontSize: '11px', fontWeight: 'bold' }}
                />
                <Line 
                    type="monotone" 
                    dataKey="total" 
                    stroke="var(--color-accent)" 
                    strokeWidth={3} 
                    dot={false}
                    activeDot={{ r: 5, fill: 'var(--color-accent)', strokeWidth: 0 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>
    </div>
  );
}
