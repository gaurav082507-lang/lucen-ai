import React from "react";
import type { Evidence } from "../api/types";
import { Crosshair } from "lucide-react";

interface Props {
  evidence: Evidence;
  isActive?: boolean;
  onSelect?: (ev: Evidence) => void;
}

export const EvidenceCard: React.FC<Props> = ({ evidence, isActive = false, onSelect }) => {
  const isRisk = evidence.kind === "risk";
  const probPercent = Math.round(evidence.calibrated_score * 100);

  const severityBadge = {
    high: "bg-rose-500/15 text-rose-400 border-rose-500/30",
    medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    low: "bg-sky-500/15 text-sky-400 border-sky-500/30",
  }[evidence.severity];

  return (
    <div
      onClick={() => onSelect && onSelect(evidence)}
      className={`p-4 rounded-xl border transition-all cursor-pointer ${
        isActive
          ? "bg-slate-800/90 border-sky-500 shadow-md shadow-sky-500/10 ring-1 ring-sky-500/50"
          : "bg-slate-900/60 border-slate-800 hover:bg-slate-850 hover:border-slate-700"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs font-semibold text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
            {evidence.id}
          </span>
          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${severityBadge}`}>
            {evidence.severity}
          </span>
          <span className="text-xs text-slate-500 font-mono">
            {evidence.source}
          </span>
        </div>

        {evidence.bbox && (
          <span className="flex items-center gap-1 text-[11px] font-medium text-sky-400 hover:text-sky-300">
            <Crosshair className="w-3.5 h-3.5" />
            <span>Region</span>
          </span>
        )}
      </div>

      <h4 className="mt-2 text-sm font-semibold text-slate-100 flex items-center gap-1.5">
        {evidence.title}
      </h4>

      <p className="mt-1 text-xs text-slate-300 leading-relaxed">
        {evidence.reason}
      </p>

      {/* Progress & metrics */}
      {isRisk && (
        <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
          <div className="flex-1 mr-4">
            <div className="flex justify-between text-[11px] text-slate-400 mb-1">
              <span>Risk Probability</span>
              <span className="font-mono font-medium text-slate-200">{probPercent}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  evidence.severity === "high"
                    ? "bg-rose-500"
                    : evidence.severity === "medium"
                    ? "bg-amber-500"
                    : "bg-sky-500"
                }`}
                style={{ width: `${probPercent}%` }}
              />
            </div>
          </div>

          <div className="text-right text-[11px] text-slate-400 font-mono">
            <span>Weight: </span>
            <span className="text-slate-200 font-semibold">{evidence.effective_weight.toFixed(2)}</span>
          </div>
        </div>
      )}
    </div>
  );
};
