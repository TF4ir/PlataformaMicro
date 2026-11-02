---
trigger: always_on
description: Reglas para PostgreSQL, Supabase, RLS y diseño relacional.
---
# Reglas de Base de Datos

1. **Claves Primarias y Tiempos:** Toda tabla debe contar con un UUID como clave primaria (`id uuid DEFAULT gen_random_uuid() PRIMARY KEY`) y campos `created_at timestamptz DEFAULT now() NOT NULL`.
2. **Row Level Security (RLS) Obligatorio:** Ninguna tabla se crea sin habilitar `ALTER TABLE x ENABLE ROW LEVEL SECURITY;`.
3. **Privilegio Mínimo:**
   - Los estudiantes solo pueden leer y crear registros vinculados a su propio `auth.uid()`.
   - Los docentes solo pueden visualizar las secciones y alumnos a los que están formalmente asignados en `enrollments` / `sections`.
4. **Integridad Referencial:** Todas las claves foráneas deben tener restricciones explícitas (`ON DELETE RESTRICT` o `CASCADE` según la criticidad del registro histórico).
5. **Inmutabilidad de `answer_events`:** Denegar explícitamente operaciones `UPDATE` y `DELETE` para el rol anónimo y autenticado sobre la tabla `answer_events`.
