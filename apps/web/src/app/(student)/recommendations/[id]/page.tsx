"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, Clock, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  getStudentRecommendations,
  RecommendationItemResponse,
} from "@/lib/api/recommendations";

interface Props {
  params: {
    id: string;
  };
}

export default function RecommendationPrelaunchPage({ params }: Props) {
  const [recommendation, setRecommendation] = useState<RecommendationItemResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const list = await getStudentRecommendations(true);
        const match = list.find((r) => r.id === params.id || r.microcontent.id === params.id);
        if (match) {
          setRecommendation(match);
        }
      } catch (err) {
        console.error("Error loading recommendation:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.id]);

  const targetMicrocontentId =
    recommendation?.microcontent?.id || "a1000000-0000-0000-0000-000000000001";
  const title = recommendation?.microcontent?.title || "Fotosíntesis: Fase luminosa y fijación de carbono";
  const kcName = recommendation?.knowledge_component_name || "Fotosíntesis";
  const durationMinutes = recommendation
    ? Math.ceil(recommendation.microcontent.estimated_duration_seconds / 60)
    : 8;

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Back button */}
      <div>
        <Link
          href="/recommendations"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Volver a recomendaciones
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
          Refuerzo de {kcName}
        </h1>
        <p className="text-slate-500 text-sm max-w-xl mx-auto leading-relaxed">
          Diseñado para consolidar los conceptos clave antes de que decaiga tu memoria de recuperación.
        </p>
      </div>

      {/* Hero Card */}
      <Card className="rounded-3xl border-slate-200/80 overflow-hidden shadow-sm bg-white grid grid-cols-1 md:grid-cols-12 mt-6">
        {/* Left Side: Botanical Illustration Area */}
        <div className="md:col-span-5 bg-[#edf8f5] p-8 flex items-center justify-center border-b md:border-b-0 md:border-r border-[#d1fae5]/60 min-h-[280px]">
          <div className="relative flex flex-col items-center">
            <svg className="w-40 h-52" viewBox="0 0 100 140" fill="none">
              <ellipse cx="50" cy="130" rx="44" ry="10" fill="#854d0e" opacity="0.6" />
              <path
                d="M50 128 V 50"
                stroke="#15803d"
                strokeWidth="5"
                strokeLinecap="round"
              />
              <path
                d="M50 100 C 25 95, 10 75, 18 60 C 32 60, 48 85, 50 100 Z"
                fill="#22c55e"
                stroke="#15803d"
                strokeWidth="2.5"
              />
              <path
                d="M50 78 C 75 72, 90 50, 80 35 C 68 35, 54 60, 50 78 Z"
                fill="#16a34a"
                stroke="#15803d"
                strokeWidth="2.5"
              />
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
              Ciencias · Microaprendizaje adaptativo
            </p>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              {title}
            </h2>
            <p className="text-xs leading-relaxed text-slate-600">
              Revisarás las estructuras celulares, los reactivos y productos esenciales en una lección concisa con telemetría de exposición activa.
            </p>
          </div>

          {/* Empathetic Box */}
          <div className="rounded-2xl bg-teal-50/70 border border-teal-100 p-4">
            <p className="text-xs text-teal-900 leading-relaxed font-medium">
              💡 {recommendation?.decision_reason || "Un repaso oportuno fortalece las vías de recuperación de la memoria antes de tu siguiente evaluación."}
            </p>
          </div>

          {/* Steps Preview */}
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-3">
                <div className="h-6 w-6 rounded-full bg-teal-600 text-white flex items-center justify-center text-xs font-bold">
                  1
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-900">Lectura activa de conceptos</h4>
                  <p className="text-[11px] text-slate-500">{durationMinutes} min estimados</p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-3">
                <div className="h-6 w-6 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center text-xs font-bold">
                  2
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-900">Verificación formativa</h4>
                  <p className="text-[11px] text-slate-500">Preguntas de retención espaciada</p>
                </div>
              </div>
            </div>
          </div>

          {/* Launch Button */}
          <div className="pt-2">
            <Link
              href={`/learn/${targetMicrocontentId}?recommendation_id=${params.id}`}
              className="block"
            >
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
          Duración aproximada: {durationMinutes} minutos. El avance se registra automáticamente en el historial de retención.
        </span>
      </div>
    </div>
  );
}
