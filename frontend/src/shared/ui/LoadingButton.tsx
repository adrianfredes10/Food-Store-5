import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  children: React.ReactNode;
}

export function LoadingButton({ isLoading, children, className = "", disabled, ...props }: LoadingButtonProps) {
  return (
    <button
      className={`relative inline-flex items-center justify-center transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed active:scale-95 ${className}`}
      disabled={isLoading || disabled}
      {...props}
    >
      {isLoading && (
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      )}
      {children}
    </button>
  );
}
