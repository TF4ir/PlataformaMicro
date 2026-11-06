#!/usr/bin/env python3
"""Migración y Seed de Base de Datos Remota — Plataforma Nexo.

Aplica sobre la base de datos remota de Supabase:
1. Reparación de tokens en auth.users (evita el error 500 de GoTrue).
2. Migraciones 2 a 8 (content_generation_jobs, question_drafts, notifications,
   activity_sections, content_exposure_events, status en activities, RLS, etc.).
3. Seed base (tenant San Agustín, docente Ana, estudiante Lucía).
4. Seed demo (10 estudiantes seudonimizados, 5 KC, 15 preguntas, 120 intentos,
   360 respuestas inmutables, 60 eventos de exposición, 30 recomendaciones).

Uso:
    SUPABASE_DB_URL='postgresql://postgres.<ref>:<password>@<host>:5432/postgres' \\
        services/ml-api/.venv/bin/python scripts/migrate_remote.py --yes

O usando Supabase Dashboard:
    Copiar y pegar el contenido de supabase/remote_migration_and_seed.sql
    en el SQL Editor y presionar RUN.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
MIGRATION_SQL = ROOT / "supabase" / "remote_migration_and_seed.sql"
LOCAL_DB_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

SUMMARY_SQL = """
SELECT 'estudiantes' AS entidad, count(*)::text AS total FROM profiles WHERE role = 'student'
UNION ALL SELECT 'docentes', count(*)::text FROM profiles WHERE role = 'teacher'
UNION ALL SELECT 'matriculas', count(*)::text FROM enrollments
UNION ALL SELECT 'componentes_kc', count(*)::text FROM knowledge_components
UNION ALL SELECT 'microcontenidos', count(*)::text FROM microcontents
UNION ALL SELECT 'preguntas', count(*)::text FROM questions
UNION ALL SELECT 'actividades', count(*)::text FROM activities
UNION ALL SELECT 'intentos', count(*)::text FROM quiz_attempts
UNION ALL SELECT 'respuestas_inmutables', count(*)::text FROM answer_events
UNION ALL SELECT 'exposiciones_inmutables', count(*)::text FROM content_exposure_events
UNION ALL SELECT 'recomendaciones', count(*)::text FROM recommendations;
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aplica la migración y seed remoto de Nexo.")
    parser.add_argument(
        "--db-url",
        default=os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL") or LOCAL_DB_URL,
        help="Cadena de conexión PostgreSQL (SUPABASE_DB_URL o DATABASE_URL).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirmación requerida para aplicar contra base remota.",
    )
    return parser.parse_args()


def is_local(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1", "host.docker.internal"}


async def run(db_url: str) -> None:
    try:
        import asyncpg
    except ModuleNotFoundError:
        raise SystemExit(
            "Falta la dependencia 'asyncpg'. Instálala o ejecuta usando:\n"
            "  services/ml-api/.venv/bin/python scripts/migrate_remote.py --yes"
        )

    if not MIGRATION_SQL.exists():
        raise SystemExit(f"No se encontró el script SQL: {MIGRATION_SQL}")

    print(f"Leyendo {MIGRATION_SQL.relative_to(ROOT)} ({MIGRATION_SQL.stat().st_size / 1024:.1f} KB)...")
    sql_content = MIGRATION_SQL.read_text(encoding="utf-8")

    print("Conectando a la base de datos...")
    conn = await asyncpg.connect(db_url)
    try:
        print("Ejecutando migración + reparación de auth + seed demo...")
        await conn.execute(sql_content)
        print("✓ Migración y seed ejecutados exitosamente.\n")

        rows = await conn.fetch(SUMMARY_SQL)
        print("Resumen de entidades en la base de datos:")
        width = max(len(r["entidad"]) for r in rows)
        for row in rows:
            print(f"  {row['entidad']:<{width}}  {row['total']:>5}")
    finally:
        await conn.close()


def main() -> int:
    args = parse_args()

    if not is_local(args.db_url) and not args.yes:
        host = urlparse(args.db_url).hostname
        print(
            f"ERROR: '{host}' es una base remota.\n"
            "Confirma explícitamente con --yes:\n"
            "  services/ml-api/.venv/bin/python scripts/migrate_remote.py --db-url '...' --yes",
            file=sys.stderr,
        )
        return 2

    host_name = "Supabase local" if is_local(args.db_url) else urlparse(args.db_url).hostname
    print(f"Destino: {host_name}")
    asyncio.run(run(args.db_url))
    print("\n✓ Proceso completado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
