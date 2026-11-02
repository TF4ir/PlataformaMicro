# AGENTS.md — Subsistema de Persistencia y Base de Datos (`supabase/`)

## 1. Misión y Alcance
Gestión del motor de base de datos relacional PostgreSQL 15+, autenticación de usuarios (Supabase Auth), almacenamiento y políticas declarativas de seguridad a nivel de fila (Row Level Security - RLS).

## 2. Estructura de Directorios
- `config.toml`: Configuración del entorno local de Supabase CLI.
- `migrations/`: Scripts de migración SQL secuenciales, idempotentes y versionados (`YYYYMMDDHHMMSS_*.sql`).
- `seed.sql`: Datos semilla reproducibles con datos seudonimizados para pruebas locales.
- `tests/`: Pruebas de políticas RLS y triggers de integridad referencial.

## 3. Reglas de Persistencia y Seguridad
1. **Identificadores y Trazabilidad:** Toda tabla debe tener clave primaria UUID generada con `gen_random_uuid()` y campos `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`.
2. **Row Level Security (RLS) Obligatorio al 100%:** Ninguna tabla se crea sin ejecutar `ALTER TABLE <tabla> ENABLE ROW LEVEL SECURITY;`.
3. **Principio de Privilegio Mínimo:**
   - Estudiantes (`student`): Únicamente pueden consultar y crear registros vinculados a su propio `auth.uid()`.
   - Docentes (`teacher`): Únicamente pueden visualizar secciones y métricas de estudiantes asignados en `enrollments`/`sections`.
   - Rol anónimo (`anon`): Sin acceso a registros educativos privados.
4. **Inmutabilidad de `answer_events`:** La tabla de eventos de interacción es Append-Only. Se debe denegar explícitamente `UPDATE` y `DELETE` para roles `anon` y `authenticated`.
5. **Disociación de Identidad de Menores:** La información personal residirá en `profiles` vinculada a `auth.users`, pero el vínculo analítico con interacciones y recomendaciones se realiza mediante `student_id_pseudo UUID DEFAULT gen_random_uuid()` en `enrollments`.
6. **Integridad Referencial:** Declarar explícitamente `ON DELETE RESTRICT` para entidades históricas y `ON DELETE CASCADE` solo cuando la eliminación dependa del ciclo de vida del contenedor padre.
