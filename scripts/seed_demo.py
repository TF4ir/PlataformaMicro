#!/usr/bin/env python3
"""Seed de demostración para la Plataforma de Microaprendizaje Adaptativo (NEXO).

Ejecuta, en orden y de forma idempotente:

1. ``supabase/seed.sql``       -- tenant, docente, estudiante Lucía, curso,
                                  sección, unidades y contenido canónico.
2. ``supabase/seed_demo.sql``  -- 10 estudiantes seudonimizados, 5 KC,
                                  5 microcontenidos, 15 preguntas, 5 actividades
                                  y 6 semanas de historial observado.

Uso local (Supabase CLI):

    python scripts/seed_demo.py

Uso contra un proyecto remoto (requiere la cadena de conexión Postgres):

    SUPABASE_DB_URL='postgresql://postgres.<ref>:<password>@aws-0-...:5432/postgres' \\
        python scripts/seed_demo.py --yes

El script nunca borra datos. Los UUID son deterministas, por lo que volver a
ejecutarlo no duplica estudiantes, intentos, respuestas ni recomendaciones.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
BASE_SEED = ROOT / "supabase" / "seed.sql"
DEMO_SEED = ROOT / "supabase" / "seed_demo.sql"
LOCAL_DB_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

SUMMARY_SQL = """
SELECT 'estudiantes' AS entidad, count(*)::text AS total FROM profiles WHERE role = 'student'
UNION ALL SELECT 'matriculas', count(*)::text FROM enrollments
UNION ALL SELECT 'componentes_kc', count(*)::text FROM knowledge_components
UNION ALL SELECT 'microcontenidos', count(*)::text FROM microcontents
UNION ALL SELECT 'preguntas', count(*)::text FROM questions
UNION ALL SELECT 'actividades', count(*)::text FROM activities
UNION ALL SELECT 'intentos', count(*)::text FROM quiz_attempts
UNION ALL SELECT 'respuestas', count(*)::text FROM answer_events
UNION ALL SELECT 'exposiciones', count(*)::text FROM content_exposure_events
UNION ALL SELECT 'recomendaciones', count(*)::text FROM recommendations;
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Carga el dataset de demostración de NEXO.")
    parser.add_argument(
        "--db-url",
        default=os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL") or LOCAL_DB_URL,
        help="Cadena Postgres. Por defecto usa SUPABASE_DB_URL, DATABASE_URL o el Supabase local.",
    )
    parser.add_argument(
        "--skip-base",
        action="store_true",
        help="No ejecuta supabase/seed.sql (útil si el tenant base ya existe).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirma la ejecución contra una base remota (obligatorio si el host no es local).",
    )
    return parser.parse_args()


def is_local(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1", "host.docker.internal"}


def read_sql(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"No se encontró el archivo requerido: {path}")
    return path.read_text(encoding="utf-8")


async def run(db_url: str, skip_base: bool) -> None:
    try:
        import asyncpg
    except ModuleNotFoundError:
        raise SystemExit(
            "Falta la dependencia 'asyncpg'. Instálala con:\n"
            "  pip install asyncpg\n"
            "o usa el entorno del servicio:\n"
            "  services/ml-api/.venv/bin/python scripts/seed_demo.py"
        )

    conn = await asyncpg.connect(db_url)
    try:
        if not skip_base:
            print(f"[1/2] Aplicando {BASE_SEED.relative_to(ROOT)} ...")
            await conn.execute(read_sql(BASE_SEED))

        print(f"[2/2] Aplicando {DEMO_SEED.relative_to(ROOT)} ...")
        await conn.execute(read_sql(DEMO_SEED))

        rows = await conn.fetch(SUMMARY_SQL)
        print("\nDataset de demostración disponible:")
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
            f"ERROR: '{host}' parece una base remota.\n"
            "Confirma explícitamente la carga con --yes.\n"
            "El seed es idempotente y solo inserta datos de demostración, pero\n"
            "nunca debe ejecutarse por accidente sobre producción.",
            file=sys.stderr,
        )
        return 2

    if is_local(args.db_url):
        print("Destino: Supabase local")
    else:
        print(f"Destino: {urlparse(args.db_url).hostname} (remoto confirmado)")

    asyncio.run(run(args.db_url, args.skip_base))
    print("\nOK: seed de demostración aplicado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
