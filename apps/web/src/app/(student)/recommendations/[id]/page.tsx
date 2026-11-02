"use client";

import React from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, Clock, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { mockRecommendedActivity } from "@/lib/mock-data";

export default function RecommendationPrelaunchPage() {
  const rec = mockRecommendedActivity;

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Back button */}
      <div>
        <Link
          href="/courses"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Volver al curso
        </Link>
      </div>

      {/* Header section */}
      <div className="text-center space-y-3 pt-2">
        <Badge
          variant="lavender"
          className="px-4 py-1 text-xs gap-1.5 inline-flex"
        >
          <Sparkles className="w-3.5 h-3.5" />
          ACTIVIDAD RECOMENDADA
        </Badge>
        <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">
          {rec.title}
        </h1>
        <p className="text-slate-500 text-sm max-w-xl mx-auto leading-relaxed">
          {rec.subtitle}
        </p>
      </div>

      {/* Hero Card */}
      <Card className="rounded-3xl border-slate-200/80 overflow-hidden shadow-sm bg-white grid grid-cols-1 md:grid-cols-12 mt-6">
        {/* Left Side: Botanical Illustration Area */}
        <div className="md:col-span-5 bg-[#edf8f5] p-8 flex items-center justify-center border-b md:border-b-0 md:border-r border-[#d1fae5]/60 min-h-[280px]">
          <div className="relative flex flex-col items-center">
            {/* Plant SVG matching the capture */}
            <svg className="w-40 h-52" viewBox="0 0 100 140" fill="none">
              {/* Soil base */}
              <ellipse cx="50" cy="130" rx="44" ry="10" fill="#854d0e" opacity="0.6" />
              {/* Main Stem */}
              <path
                d="M50 128 V 50"
                stroke="#15803d"
                strokeWidth="5"
                strokeLinecap="round"
              />
              {/* Left Leaf lower */}
              <path
                d="M50 100 C 25 95, 10 75, 18 60 C 32 60, 48 85, 50 100 Z"
                fill="#22c55e"
                stroke="#15803d"
                strokeWidth="2.5"
              />
              {/* Right Leaf middle */}
              <path
                d="M50 78 C 75 72, 90 50, 80 35 C 68 35, 54 60, 50 78 Z"
                fill="#16a34a"
                stroke="#15803d"
                strokeWidth="2.5"
              />
              {/* Top Leaves */}
              <path
                d="M50 50 C 40 28, 48 15, 55 10 C 62 15, 62 32, 50 50 Z"
                fill="#34d399"
                stroke="#15803d"
                strokeWidth="2"
              />
            </svg>
          </div>
        </div>

        {/* Right Side: Activity Details & Steps */}
        <div className="md:col-span-7 p-6 md:p-8 flex flex-col justify-between space-y-6">
          <div className="space-y-3">
            <p className="text-[11px] font-bold uppercase tracking-wider text-teal-700">
              {rec.courseTitle} · {rec.unitTitle}
            </p>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              {rec.conceptTitle}
            </h2>
            <p className="text-xs leading-relaxed text-slate-600">
              Repasarás cómo las plantas transforman la energía luminosa en energía
              química y qué elementos intervienen en el proceso.
            </p>
          </div>

          {/* Empathetic Lavender Box */}
          <div className="rounded-2xl bg-[#f5f3ff] p-4 border border-[#ede9fe] space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#6d28d9]">
              <Sparkles className="w-3.5 h-3.5" />
              <span>¿Por qué te lo recomendamos?</span>
            </div>
            <p className="text-[11px] leading-relaxed text-[#5b21b6]">
              {rec.whyRecommended}
            </p>
          </div>

          {/* Steps Breakdown */}
          <div className="space-y-2.5 pt-1">
            {rec.steps.map((step) => (
              <div
                key={step.number}
                className="flex items-center justify-between p-3 rounded-xl border border-slate-100 bg-slate-50/70"
              >
                <div className="flex items-center gap-3">
                  <div className="h-7 w-7 rounded-lg bg-teal-100 text-teal-800 text-xs font-bold flex items-center justify-center">
                    {step.number}
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">
                      {step.title}
                    </h4>
                    <p className="text-[11px] text-slate-500">{step.duration}</p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </div>
            ))}
          </div>

          {/* Launch Button */}
          <div className="pt-2">
            <Link href="/learn/rec-fotosintesis" className="block">
              <Button
                size="lg"
                className="w-full bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl gap-2 shadow-sm h-12 transition-all"
              >
                Comenzar actividad
                <ChevronRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </div>
      </Card>

      {/* Footer Info */}
      <div className="flex items-center justify-center gap-2 text-xs text-slate-500 pt-2">
        <Clock className="w-3.5 h-3.5" />
        <span>
          Duración aproximada: {rec.estimatedMinutes} minutos. Puedes pausar y
          continuar después.
        </span>
      </div>
    </div>
  );
}
