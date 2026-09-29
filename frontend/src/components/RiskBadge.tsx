import React from "react";
import { ShieldCheck, AlertTriangle, ShieldAlert } from "lucide-react";
import type { RiskBand } from "../api/types";

interface Props {
  band: RiskBand;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const RiskBadge: React.FC<Props> = ({ band, size = "md", className = "" }) => {
  const configs = {
    LOW: {
      label: "LOW FRAUD RISK",
      icon: ShieldCheck,
      classes: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    },
    MEDIUM: {
      label: "SUSPICIOUS / REVIEW",
      icon: AlertTriangle,
      classes: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    },
    HIGH: {
      label: "HIGH FRAUD RISK",
      icon: ShieldAlert,
      classes: "bg-rose-500/15 text-rose-400 border-rose-500/30 animate-pulse",
    },
  };

  const current = configs[band] || configs.LOW;
  const Icon = current.icon;

  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs gap-1",
    md: "px-2.5 py-1 text-xs font-semibold gap-1.5",
    lg: "px-3.5 py-1.5 text-sm font-bold gap-2",
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-full border shadow-sm tracking-wide uppercase ${current.classes} ${sizeClasses} ${className}`}
    >
      <Icon className={size === "lg" ? "w-4 h-4" : "w-3.5 h-3.5"} />
      <span>{current.label}</span>
    </span>
  );
};
