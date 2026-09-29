import React, { useState } from "react";
import { Sliders, Eye, EyeOff } from "lucide-react";
import type { BBox } from "../api/types";

interface Props {
  originalSrc: string;
  heatmapSrc?: string;
  activeBBox?: BBox | null;
}

export const ImageViewer: React.FC<Props> = ({ originalSrc, heatmapSrc, activeBBox }) => {
  const [heatmapOpacity, setHeatmapOpacity] = useState<number>(0.65);
  const [showHeatmap, setShowHeatmap] = useState<boolean>(true);
  const [mode, setMode] = useState<"overlay" | "split">("overlay");

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden flex flex-col">
      {/* Viewer Toolbar */}
      <div className="p-3 bg-slate-950/70 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMode("overlay")}
            className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
              mode === "overlay"
                ? "bg-sky-500 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            }`}
          >
            Overlay Mode
          </button>
          <button
            onClick={() => setMode("split")}
            className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
              mode === "split"
                ? "bg-sky-500 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            }`}
          >
            Side-by-Side
          </button>
        </div>

        {heatmapSrc && mode === "overlay" && (
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowHeatmap(!showHeatmap)}
              className="flex items-center gap-1 text-slate-300 hover:text-white"
            >
              {showHeatmap ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
              <span>Heatmap</span>
            </button>

            {showHeatmap && (
              <div className="flex items-center gap-2">
                <Sliders className="w-3.5 h-3.5 text-slate-400" />
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={heatmapOpacity}
                  onChange={(e) => setHeatmapOpacity(parseFloat(e.target.value))}
                  className="w-24 h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-sky-500"
                />
                <span className="font-mono text-slate-400 w-8">{Math.round(heatmapOpacity * 100)}%</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Media Canvas */}
      <div className="relative p-4 flex items-center justify-center min-h-[380px] max-h-[520px] bg-slate-950/40 overflow-hidden">
        {mode === "overlay" ? (
          <div className="relative max-w-full max-h-[480px] inline-block select-none">
            <img
              src={originalSrc}
              alt="Claim Original"
              className="max-h-[480px] max-w-full object-contain rounded-lg border border-slate-800"
            />

            {heatmapSrc && showHeatmap && (
              <img
                src={heatmapSrc}
                alt="Forensic Heatmap"
                className="absolute inset-0 max-h-[480px] max-w-full object-contain rounded-lg pointer-events-none transition-opacity duration-200"
                style={{ opacity: heatmapOpacity }}
              />
            )}

            {/* Active highlighted BBox */}
            {activeBBox && (
              <div
                className="absolute border-2 border-rose-500 bg-rose-500/20 rounded shadow-lg pointer-events-none animate-pulse"
                style={{
                  left: `${activeBBox.x * 100}%`,
                  top: `${activeBBox.y * 100}%`,
                  width: `${activeBBox.w * 100}%`,
                  height: `${activeBBox.h * 100}%`,
                }}
              >
                <span className="absolute -top-5 left-0 px-1.5 py-0.2 bg-rose-600 text-white text-[10px] font-mono rounded">
                  Flagged Region
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full h-full max-h-[480px]">
            <div className="flex flex-col items-center">
              <span className="text-xs font-semibold text-slate-400 mb-2">Original Capture</span>
              <img
                src={originalSrc}
                alt="Original"
                className="max-h-[420px] object-contain rounded-lg border border-slate-800"
              />
            </div>
            {heatmapSrc && (
              <div className="flex flex-col items-center">
                <span className="text-xs font-semibold text-slate-400 mb-2">Forensic ELA Heatmap</span>
                <img
                  src={heatmapSrc}
                  alt="Heatmap"
                  className="max-h-[420px] object-contain rounded-lg border border-slate-800"
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
