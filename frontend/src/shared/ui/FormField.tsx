import React from "react";

interface FormFieldProps {
  label: string;
  error?: string;
  children: React.ReactNode;
  className?: string;
}

export function FormField({ label, error, children, className = "" }: FormFieldProps) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <label className="text-sm font-medium text-slate-700">{label}</label>
      {children}
      {error && <span className="text-sm text-danger mt-1">{error}</span>}
    </div>
  );
}
