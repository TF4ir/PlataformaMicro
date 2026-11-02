import React from "react";
import { Sparkles, Sun } from "lucide-react";

export function PhotosynthesisDiagram() {
  return (
    <div className="relative w-full rounded-2xl bg-[#edf8f5] p-6 md:p-10 flex flex-col items-center justify-center border border-[#d1fae5]/60 overflow-hidden">
      {/* Top Tag: CO2 */}
      <div className="mb-4">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-[#f3e8ff] px-3.5 py-1 text-xs font-medium text-[#7e22ce] shadow-xs border border-purple-200/60">
          <span className="h-1.5 w-1.5 rounded-full bg-[#a855f7]" />
          CO₂ · Dióxido de carbono
        </span>
      </div>

      {/* Main Diagram Center Flow */}
      <div className="flex w-full max-w-lg items-center justify-between gap-4 py-2">
        {/* Left: Solar light */}
        <div className="flex flex-col items-center text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[#fde68a] text-[#b45309] shadow-sm ring-4 ring-amber-100">
            <Sun className="h-7 w-7 text-[#d97706] animate-pulse" />
          </div>
          <span className="mt-2 text-xs font-semibold text-slate-700">Luz solar</span>
        </div>

        {/* Arrow to Plant */}
        <div className="flex items-center text-emerald-600 font-bold">
          <svg className="w-8 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </div>

        {/* Center: The Plant Graphic */}
        <div className="relative flex flex-col items-center">
          <svg className="w-24 h-36" viewBox="0 0 100 140" fill="none">
            {/* Stem */}
            <path d="M50 130 V 40" stroke="#15803d" strokeWidth="4" strokeLinecap="round" />
            {/* Left Leaf */}
            <path
              d="M50 85 C 30 80, 20 60, 25 45 C 35 45, 48 65, 50 85 Z"
              fill="#22c55e"
              stroke="#15803d"
              strokeWidth="2"
            />
            {/* Right Leaf */}
            <path
              d="M50 65 C 70 60, 80 40, 75 25 C 65 25, 52 45, 50 65 Z"
              fill="#16a34a"
              stroke="#15803d"
              strokeWidth="2"
            />
            {/* Top Leaf */}
            <path
              d="M50 40 C 45 20, 50 10, 55 5 C 60 10, 60 25, 50 40 Z"
              fill="#34d399"
              stroke="#15803d"
              strokeWidth="2"
            />
            {/* Base / Soil hint */}
            <ellipse cx="50" cy="132" rx="35" ry="6" fill="#854d0e" opacity="0.4" />
          </svg>
        </div>

        {/* Arrow to Products */}
        <div className="flex items-center text-emerald-600 font-bold">
          <svg className="w-8 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </div>

        {/* Right: Products Cards */}
        <div className="flex flex-col gap-2.5">
          <div className="rounded-xl border border-slate-200/90 bg-white px-3.5 py-1.5 shadow-xs">
            <p className="text-sm font-bold text-slate-900">O₂</p>
            <p className="text-[11px] text-slate-500">Oxígeno</p>
          </div>
          <div className="rounded-xl border border-slate-200/90 bg-white px-3.5 py-1.5 shadow-xs">
            <p className="text-sm font-bold text-slate-900">C₆H₁₂O₆</p>
            <p className="text-[11px] text-slate-500">Glucosa</p>
          </div>
        </div>
      </div>

      {/* Bottom Tag: H2O */}
      <div className="mt-4">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-[#e0f2fe] px-3.5 py-1 text-xs font-medium text-[#0369a1] shadow-xs border border-sky-200/60">
          <span className="h-1.5 w-1.5 rounded-full bg-[#0284c7]" />
          H₂O · Agua
        </span>
      </div>
    </div>
  );
}
