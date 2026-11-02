"use client";

import React, { useState } from "react";
import {
  Plus,
  Search,
  ChevronDown,
  Sparkles,
  BookOpen,
  MoreHorizontal,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockCourses } from "@/lib/mock-data";

export default function TeacherCoursesPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const courses = mockCourses.filter((course) => {
    const matchesSearch =
      course.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      course.grade.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "active" && course.status === "active") ||
      (statusFilter === "draft" && course.status === "draft");
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-8 pb-12">
      {/* Header with + Nuevo Curso CTA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-[#0A635F]">
            CONTENIDO
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Gestión de cursos
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Crea, organiza y publica experiencias de aprendizaje.
          </p>
        </div>

        <div>
          <Button
            size="lg"
            className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl gap-2 shadow-sm transition-all"
          >
            <Plus className="w-4 h-4" />
            Nuevo curso
          </Button>
        </div>
      </div>

      {/* Filter Row: Search & Status Dropdown */}
      <div className="flex flex-col sm:flex-row items-center gap-4">
        <div className="relative flex-1 w-full max-w-sm">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar curso"
            className="w-full h-10 pl-10 pr-4 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-600/30 text-slate-800 placeholder:text-slate-400"
          />
        </div>

        <div className="relative w-full sm:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full sm:w-auto appearance-none bg-white border border-slate-200 text-slate-700 text-xs font-semibold rounded-xl pl-4 pr-10 py-2.5 shadow-xs focus:outline-none focus:ring-2 focus:ring-teal-600/30"
          >
            <option value="all">Todos los estados</option>
            <option value="active">Activos</option>
            <option value="draft">Borradores</option>
          </select>
          <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      {/* Courses Table Card */}
      <Card className="rounded-3xl border-slate-200/80 shadow-xs bg-white overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 uppercase font-bold tracking-wider text-[10px] bg-slate-50/50">
                <th className="py-4 pl-6 pr-4 font-semibold">CURSO</th>
                <th className="py-4 px-4 font-semibold">ESTADO</th>
                <th className="py-4 px-4 font-semibold">CONTENIDO</th>
                <th className="py-4 px-4 font-semibold">SECCIONES</th>
                <th className="py-4 px-4 font-semibold">ACTUALIZADO</th>
                <th className="py-4 pr-6 pl-4 text-right font-semibold">ACCIONES</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {courses.map((course) => (
                <tr
                  key={course.id}
                  className="hover:bg-slate-50/60 transition-colors"
                >
                  {/* Course Title + Subtitle */}
                  <td className="py-4 pl-6 pr-4">
                    <div className="flex items-center gap-3.5">
                      <div
                        className={`h-9 w-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
                          course.status === "active"
                            ? "bg-teal-50 text-teal-700"
                            : "bg-purple-50 text-purple-700"
                        }`}
                      >
                        {course.status === "active" ? (
                          <Sparkles className="w-4 h-4" />
                        ) : (
                          <BookOpen className="w-4 h-4" />
                        )}
                      </div>
                      <div>
                        <p className="font-bold text-slate-900 text-sm">
                          {course.title}
                        </p>
                        <p className="text-[11px] text-slate-400">
                          {course.grade}
                        </p>
                      </div>
                    </div>
                  </td>

                  {/* Estado */}
                  <td className="py-4 px-4">
                    <Badge
                      variant={course.status === "active" ? "active" : "draft"}
                      className="text-[11px] font-semibold"
                    >
                      {course.status === "active" ? "Activo" : "Borrador"}
                    </Badge>
                  </td>

                  {/* Contenido */}
                  <td className="py-4 px-4 font-medium text-slate-600">
                    {course.unitsCount > 0
                      ? `${course.unitsCount} unidades · ${course.conceptsCount} conceptos`
                      : "Sin contenido"}
                  </td>

                  {/* Secciones */}
                  <td className="py-4 px-4 font-medium text-slate-600">
                    {course.sectionsCount > 0
                      ? `${course.sectionsCount} secciones`
                      : "—"}
                  </td>

                  {/* Actualizado */}
                  <td className="py-4 px-4 text-slate-500 font-medium">
                    {course.lastUpdated}
                  </td>

                  {/* Acciones */}
                  <td className="py-4 pr-6 pl-4 text-right">
                    <button
                      className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
                      title="Opciones de curso"
                    >
                      <MoreHorizontal className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
