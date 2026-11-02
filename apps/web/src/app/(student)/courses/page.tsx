"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Sparkles, ChevronRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { mockCourses } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export default function CoursesPage() {
  const [filter, setFilter] = useState<"todos" | "en_curso" | "completados">(
    "todos"
  );

  const mainCourse = mockCourses[0];

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-teal-700">
          APRENDIZAJE
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
          Mis cursos
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Explora tus cursos asignados y continúa aprendiendo.
        </p>
      </div>

      {/* Filter Tabs & Counter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200/80">
          <button
            onClick={() => setFilter("todos")}
            className={cn(
              "px-4 py-1.5 text-xs font-semibold rounded-lg transition-all",
              filter === "todos"
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            )}
          >
            Todos
          </button>
          <button
            onClick={() => setFilter("en_curso")}
            className={cn(
              "px-4 py-1.5 text-xs font-semibold rounded-lg transition-all",
              filter === "en_curso"
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            )}
          >
            En curso
          </button>
          <button
            onClick={() => setFilter("completados")}
            className={cn(
              "px-4 py-1.5 text-xs font-semibold rounded-lg transition-all",
              filter === "completados"
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            )}
          >
            Completados
          </button>
        </div>

        <p className="text-xs font-medium text-slate-500">1 curso asignado</p>
      </div>

      {/* Main Grid: Course Card + Info Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Course Card (8 cols) */}
        <div className="lg:col-span-8">
          <Link href="/recommendations/rec-fotosintesis" className="block group">
            <Card className="rounded-3xl border-slate-200/80 overflow-hidden shadow-xs hover:border-teal-300 hover:shadow-md transition-all flex flex-col md:flex-row">
              {/* Dark Left Area with Atomic Graphic */}
              <div className="md:w-56 bg-[#092624] p-6 text-white flex flex-col justify-between items-center relative overflow-hidden min-h-[180px]">
                <Badge
                  variant="active"
                  className="bg-teal-900/80 text-teal-200 border border-teal-700/50 self-start text-[10px]"
                >
                  EN CURSO
                </Badge>

                {/* Atomic Orbit Graphic */}
                <div className="my-auto relative flex items-center justify-center py-4">
                  <div className="w-28 h-16 rounded-full border border-teal-400/50 transform -rotate-12 flex items-center justify-center">
                    <div className="w-28 h-16 rounded-full border border-teal-400/50 transform rotate-45 flex items-center justify-center">
                      <span className="text-xs font-extrabold uppercase tracking-widest text-white transform -rotate-33">
                        CIENCIAS
                      </span>
                    </div>
                  </div>
                </div>

                <div className="h-4" />
              </div>

              {/* Right Course Information */}
              <div className="flex-1 p-6 md:p-8 flex flex-col justify-between space-y-6">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-wider text-teal-700">
                    {mainCourse.area}
                  </p>
                  <h2 className="text-2xl font-bold text-slate-900 group-hover:text-teal-700 transition-colors mt-1">
                    {mainCourse.title}
                  </h2>
                  <p className="text-sm text-slate-500 mt-1">
                    {mainCourse.description}
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-slate-600">Progreso del curso</span>
                      <span className="text-slate-900">{mainCourse.progressPercentage}%</span>
                    </div>
                    <Progress value={mainCourse.progressPercentage} className="h-2" />
                  </div>

                  <div className="pt-2 flex items-center justify-between text-xs font-medium text-slate-500 border-t border-slate-100">
                    <span>
                      {mainCourse.unitsCount} unidades · {mainCourse.conceptsCount} conceptos
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600 group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              </div>
            </Card>
          </Link>
        </div>

        {/* Right Info Card: Adaptive Pedagogical Assurance (4 cols) */}
        <div className="lg:col-span-4">
          <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs space-y-4 bg-white">
            <div className="h-10 w-10 rounded-xl bg-purple-100 text-[#7c3aed] flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>

            <h3 className="text-base font-bold text-slate-900 leading-snug">
              Tu aprendizaje se adapta contigo
            </h3>

            <p className="text-xs leading-relaxed text-slate-600">
              Las recomendaciones mejoran a medida que completas actividades. Los
              datos actuales combinan tus respuestas observadas con estimaciones
              orientativas.
            </p>

            <div className="pt-2">
              <Link
                href="/progress"
                className="text-xs font-bold text-teal-700 hover:text-teal-800 flex items-center gap-1 group"
              >
                Cómo funcionan las recomendaciones
                <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
