import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

export function GuiaPage() {
  return (
    <div className="mx-auto max-w-4xl min-w-0 px-3 py-4 fade-in sm:px-4 md:py-12">
      <header className="mb-6 md:mb-16 text-center md:text-left">
        <h1 className="text-xl md:text-5xl font-black text-slate-950 font-outfit tracking-tighter uppercase mb-2 md:mb-4">GUÍA DE OPERACIONES</h1>
        <p className="text-[9px] md:text-[11px] font-black text-slate-400 uppercase tracking-[0.3em] leading-relaxed">Protocolos de uso para perfiles de cliente y administración.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-12">
        {/* Admin Access Section */}
        <section className="bg-slate-950 text-white rounded-2xl md:rounded-[2.5rem] p-8 md:p-12 shadow-2xl shadow-slate-300 relative overflow-hidden h-full">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2 blur-2xl"></div>
            <h2 className="text-[10px] md:text-xs font-black uppercase tracking-[0.3em] font-outfit mb-8 md:mb-10 pb-4 md:pb-6 border-b border-white/10 text-slate-500">Credenciales de Auditoría</h2>
            <div className="space-y-6 md:space-y-8">
                <p className="text-[11px] md:text-sm font-bold text-slate-400 uppercase tracking-widest leading-relaxed">
                    El sistema inicializa automáticamente una cuenta de acceso total:
                </p>
                <div className="space-y-3 md:space-y-4">
                    <div className="flex flex-col sm:flex-row justify-between items-center py-2 md:py-3 border-b border-white/5 gap-1">
                        <span className="text-[8px] md:text-[9px] font-black uppercase tracking-widest text-slate-500">Identificador</span>
                        <code className="max-w-full break-all text-center text-[10px] font-mono font-bold text-white bg-white/5 px-2 py-1 rounded sm:text-xs sm:break-normal md:text-left">
                          admin@foodstore.com
                        </code>
                    </div>
                    <div className="flex flex-col sm:flex-row justify-between items-center py-2 md:py-3 border-b border-white/5 gap-1">
                        <span className="text-[8px] md:text-[9px] font-black uppercase tracking-widest text-slate-500">Clave de Acceso</span>
                        <code className="max-w-full break-all text-center text-[10px] font-mono font-bold text-white bg-white/5 px-2 py-1 rounded sm:text-xs md:text-left">
                          Admin1234!
                        </code>
                    </div>
                </div>
                <Link to="/login" className="inline-flex items-center gap-3 md:gap-4 text-white text-[9px] md:text-[10px] font-black uppercase tracking-[0.3em] hover:gap-6 transition-all pt-2 md:pt-4">
                    ACCEDER AL PORTAL <ArrowRight size={12} />
                </Link>
            </div>
        </section>

        {/* Client Flow Section */}
        <section className="bg-white rounded-2xl md:rounded-[2.5rem] premium-shadow border border-slate-50 p-8 md:p-12 h-full">
            <h2 className="text-[10px] md:text-xs font-black text-slate-950 uppercase tracking-[0.3em] font-outfit mb-8 md:mb-10 pb-4 md:pb-6 border-b border-slate-50 text-slate-500">Protocolo de Compra</h2>
            <div className="space-y-6 md:space-y-8">
                <p className="text-[11px] md:text-sm font-bold text-slate-400 uppercase tracking-widest leading-relaxed">
                    Flujo operativo optimizado para la adquisición gourmet:
                </p>
                <ol className="space-y-4 md:space-y-6">
                    <li className="flex items-start gap-3 md:gap-4">
                        <span className="text-[9px] md:text-[10px] font-black text-slate-950 bg-slate-50 w-5 h-5 md:w-6 md:h-6 rounded-lg flex items-center justify-center shrink-0">01</span>
                        <p className="text-[10px] md:text-[11px] font-black text-slate-900 uppercase tracking-widest mt-1">Catálogo de Excelencia</p>
                    </li>
                    <li className="flex items-start gap-3 md:gap-4">
                        <span className="text-[9px] md:text-[10px] font-black text-slate-950 bg-slate-50 w-5 h-5 md:w-6 md:h-6 rounded-lg flex items-center justify-center shrink-0">02</span>
                        <p className="text-[10px] md:text-[11px] font-black text-slate-900 uppercase tracking-widest mt-1">Acumulación en Cesta</p>
                    </li>
                    <li className="flex items-start gap-3 md:gap-4">
                        <span className="text-[9px] md:text-[10px] font-black text-slate-950 bg-slate-50 w-5 h-5 md:w-6 md:h-6 rounded-lg flex items-center justify-center shrink-0">03</span>
                        <p className="text-[10px] md:text-[11px] font-black text-slate-900 uppercase tracking-widest mt-1">Logística de Entrega</p>
                    </li>
                    <li className="flex items-start gap-3 md:gap-4">
                        <span className="text-[9px] md:text-[10px] font-black text-slate-950 bg-slate-50 w-5 h-5 md:w-6 md:h-6 rounded-lg flex items-center justify-center shrink-0">04</span>
                        <p className="text-[10px] md:text-[11px] font-black text-slate-900 uppercase tracking-widest mt-1">Transacción Certificada</p>
                    </li>
                </ol>
            </div>
        </section>

        {/* Admin Dashboard Section */}
        <section className="md:col-span-2 bg-white rounded-2xl md:rounded-[2.5rem] premium-shadow border border-slate-50 p-8 md:p-12 mt-2 md:mt-4 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-slate-950"></div>
            <h2 className="text-[10px] md:text-xs font-black text-slate-950 uppercase tracking-[0.3em] font-outfit mb-8 md:mb-10 pb-4 md:pb-6 border-b border-slate-50 text-slate-500">Centro de Control</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 md:gap-12">
                <div className="space-y-3 md:space-y-4">
                    <h4 className="text-[10px] md:text-[11px] font-black text-slate-950 uppercase tracking-[0.2em] font-outfit">ANÁLISIS ESTRATÉGICO</h4>
                    <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-relaxed">Monitoreo de indicadores críticos y métricas.</p>
                </div>
                <div className="space-y-3 md:space-y-4">
                    <h4 className="text-[10px] md:text-[11px] font-black text-slate-950 uppercase tracking-[0.2em] font-outfit">GESTIÓN DE ACTIVOS</h4>
                    <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-relaxed">Control centralizado del inventario y productos.</p>
                </div>
                <div className="space-y-3 md:space-y-4">
                    <h4 className="text-[10px] md:text-[11px] font-black text-slate-950 uppercase tracking-[0.2em] font-outfit">LOGÍSTICA INTEGRAL</h4>
                    <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-relaxed">Supervisión de órdenes y trazabilidad del servicio.</p>
                </div>
            </div>
            
            <div className="mt-12 md:mt-16 pt-8 md:pt-10 border-t border-slate-50">
                <p className="text-[8px] md:text-[9px] font-black text-slate-300 uppercase tracking-[0.4em] text-center">
                    SISTEMA CERTIFICADO · FOODSTORE v5.0
                </p>
            </div>
        </section>
      </div>
    </div>
  );
}
