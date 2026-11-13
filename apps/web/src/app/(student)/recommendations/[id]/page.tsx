"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Clock,
  Sparkles,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  getStudentRecommendations,
  RecommendationItemResponse,
} from "@/lib/api/recommendations";
import { resolveContentTitle, resolveKnowledgeComponentName } from "@/lib/data-provenance";

interface Props {
  params: {
    id: string;
  };
}

export default function RecommendationPrelaunchPage({ params }: Props) {
  const [recommendation, setRecommendation] = useState<RecommendationItemResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      try {
        setLoading(true);
        setError(null);
        const list = await getStudentRecommendations(true);
        const match = list.find(
          (item) => item.id === params.id || item.microcontent.id === params.id
        );

        if (isMounted) {
          if (!match) {
            setError(
              "Esta recomendación ya no está disponible o no pertenece a tu cuenta."
            );
            setRecommendation(null);
          } else {
            setRecommendation(match);
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(
            err instanceof Error
              ? err.message
              : "No se pudo cargar la recomendación."
          );
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    load();
    return () => {
      isMounted = false;
    };
  }, [params.id]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto pb-12">
        <Card className="rounded-3xl border-slate-200/80 p-8 shadow-xs bg-white space-y-4 animate-pulse">
          <div className="h-4 w-40 bg-slate-200 rounded" />
          <div className="h-8 w-80 bg-slate-200 rounded" />
          <div className="h-64 bg-slate-100 rounded-3xl" />
        </Card>
      </div>
    );
  }

  if (error || !recommendation) {
    return (
      <div className="max-w-2xl mx-auto pb-12">
        <Card className="rounded-3xl border-slate-200/80 p-8 shadow-xs bg-white text-center space-y-4">
          <div className="mx-auto h-12 w-12 rounded-2xl bg-amber-50 text-amber-700 flex items-center justify-center">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold text-slate-900">
            Recomendación no disponible
          </h1>
          <p className="text-xs text-slate-600 leading-relaxed">
            {error || "No pudimos cargar esta recomendación."}
          </p>
          <Link href="/recommendations" className="inline-block pt-2">
            <Button className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl">
              Volver a mis recomendaciones
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  const targetMicrocontentId = recommendation.microcontent.id;
  const title = resolveContentTitle(recommendation.microcontent);
  const kcName = resolveKnowledgeComponentName(
    recommendation.knowledge_component_name
  );
  const durationMinutes =
    recommendation.microcontent.estimated_duration_seconds > 0
      ? Math.max(
          1,
          Math.ceil(recommendation.microcontent.estimated_duration_seconds / 60)
        )
      : null;

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
          Revisa este contenido cuando tu plan de repaso lo indique. La duración y
          el motivo provienen de los metadatos de la recomendación.
        </p>
      </div>

      {/* Hero Card */}
      <Card className="rounded-3xl border-slate-200/80 overflow-hidden shadow-sm bg-white grid grid-cols-1 md:grid-cols-12 mt-6">
        {/* Left Side: Content-type neutral illustration */}
        <div className="md:col-span-5 bg-[#edf8f5] p-8 flex items-center justify-center border-b md:border-b-0 md:border-r border-[#d1fae5]/60 min-h-[280px]">
          <div className="h-28 w-28 rounded-3xl bg-white/80 border border-[#d1fae5] flex items-center justify-center">
            <BookOpen className="h-12 w-12 text-teal-700" />
          </div>
        </div>

        {/* Right Side: Activity Details & Steps */}
        <div className="md:col-span-7 p-6 md:p-8 flex flex-col justify-between space-y-6">
          <div className="space-y-3">
            <p className="text-[11px] font-bold uppercase tracking-wider text-teal-700">
              Microaprendizaje adaptativo
            </p>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              {title}
            </h2>
            <p className="text-xs leading-relaxed text-slate-600">
              Lección breve con registro de exposición activa. El contenido pertenece
              al componente de conocimiento indicado por la recomendación.
            </p>
          </div>

          {/* Empathetic Box */}
          <div className="rounded-2xl bg-teal-50/70 border border-teal-100 p-4">
            <p className="text-xs text-teal-900 leading-relaxed font-medium">
              {recommendation.decision_reason ||
                "El motivo de esta recomendación no fue reportado por el servicio."}
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
                  <p className="text-[11px] text-slate-500">
                    {durationMinutes !== null
                      ? `${durationMinutes} min estimados`
                      : "Duración no reportada"}
                  </p>
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
              href={`/learn/${targetMicrocontentId}?recommendation_id=${recommendation.id}`}
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
          {durationMinutes !== null
            ? `Duración aproximada: ${durationMinutes} minutos.`
            : "La duración de este contenido no está reportada."}{" "}
          El avance se registra en el historial de exposición.
        </span>
      </div>
    </div>
  );
}
