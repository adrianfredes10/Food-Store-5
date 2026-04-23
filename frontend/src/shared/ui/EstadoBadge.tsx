

const ESTADOS_CONFIG: Record<string, string> = {
  PENDIENTE: "bg-slate-100 text-slate-700 border border-slate-300",
  CONFIRMADO: "bg-blue-50 text-blue-700 border border-blue-200",
  EN_PREP: "bg-orange-50 text-orange-700 border border-orange-200",
  EN_CAMINO: "bg-yellow-50 text-yellow-700 border border-yellow-200",
  ENTREGADO: "bg-green-50 text-green-700 border border-green-200",
  CANCELADO: "bg-red-50 text-red-700 border border-red-200",
};

interface EstadoBadgeProps {
  estado: string;
  size?: "sm" | "md";
}

export function EstadoBadge({ estado, size = "md" }: EstadoBadgeProps) {
  const classes = ESTADOS_CONFIG[estado] || "bg-slate-100 text-slate-700 border border-slate-300";
  const sizeClasses = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";

  return (
    <span
      className={`inline-flex items-center justify-center rounded-full font-medium ${classes} ${sizeClasses}`}
    >
      {estado.replace("_", " ")}
    </span>
  );
}
