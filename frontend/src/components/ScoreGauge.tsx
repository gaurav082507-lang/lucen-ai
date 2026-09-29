import React from "react";
import type { RiskBand } from "../api/types";

interface Props {
  value: number; // 0.0 to 1.0
  band: RiskBand;
  label: string;
  size?: number;
  subtext?: string;
}

export const ScoreGauge: React.FC<Props> = ({
  value,
  band,
  label,
  size = 180,
  subtext,
}) => {
  const percent = Math.round(value * 100);
  const strokeWidth = size * 0.09;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - value * circumference;

  const bandColors = {
    LOW: {
      stroke: "#10b981", // Emerald
      bg: "rgba(16, 185, 129, 0.15)",
      text: "text-emerald-400",
    },
    MEDIUM: {
      stroke: "#f59e0b", // Amber
      bg: "rgba(245, 158, 11, 0.15)",
      text: "text-amber-400",
    },
    HIGH: {
      stroke: "#f43f5e", // Rose
      bg: "rgba(244, 63, 94, 0.15)",
      text: "text-rose-400",
    },
  }[band];

  return (
    <div className="flex flex-col items-center justify-center p-3">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="#1e293b"
            strokeWidth={strokeWidth}
          />
          {/* Animated score ring */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke={bandColors.stroke}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Center label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-3xl font-extrabold tracking-tight text-white font-mono">
            {percent}%
          </span>
          <span className={`text-[11px] font-bold tracking-wider uppercase ${bandColors.text}`}>
            {band}
          </span>
        </div>
      </div>

      <div className="mt-2 text-center">
        <h4 className="text-sm font-semibold text-slate-200">{label}</h4>
        {subtext && <p className="text-xs text-slate-400 mt-0.5">{subtext}</p>}
      </div>
    </div>
  );
};
