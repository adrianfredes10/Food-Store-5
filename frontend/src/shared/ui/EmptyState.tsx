import React from "react";
import { PackageOpen } from "lucide-react";
import { Link } from "react-router-dom";

interface EmptyStateProps {
  titulo: string;
  descripcion: string;
  accion?: {
    label: string;
    href: string;
  };
  icon?: React.ElementType;
}

export function EmptyState({ titulo, descripcion, accion, icon: Icon = PackageOpen }: EmptyStateProps) {
  return (
    <div className="flex min-h-[300px] flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-bg-secondary p-8 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-muted">
        <Icon className="h-8 w-8" />
      </div>
      <h3 className="mb-2 text-lg font-semibold text-primary">{titulo}</h3>
      <p className="mb-6 max-w-sm text-sm text-muted">{descripcion}</p>
      {accion && (
        <Link
          to={accion.href}
          className="inline-flex items-center justify-center rounded-lg bg-accent px-6 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:bg-accent-hover active:scale-95"
        >
          {accion.label}
        </Link>
      )}
    </div>
  );
}
