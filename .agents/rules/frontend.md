---
trigger: always_on
description: Reglas para Next.js, React, Tailwind CSS y shadcn/ui.
---
# Reglas de Frontend

1. **Next.js App Router:** Emplear Server Components por defecto. Utilizar `'use client'` únicamente cuando se requiera reactividad de UI, hooks locales o interacción de eventos.
2. **Formularios y Validación:** Todos los formularios deben gestionarse mediante `react-hook-form` acoplado con esquemas `zod`.
3. **Estilizado Consistente:** Uso mandatorio de utilidades de Tailwind CSS y primitivas de `shadcn/ui`. Prohibido el uso de estilos en línea o CSS Modules sin justificación.
4. **Lenguaje Pedagógico Empático:** La UI orientada al estudiante jamás presentará términos negativos como "Estás a punto de fallar" o "Alto riesgo de olvido". Mostrar "Refuerzo sugerido", "Concepto por consolidar" o "Momento ideal para repasar".
5. **Seguridad en Navegador:** Únicamente utilizar `NEXT_PUBLIC_SUPABASE_URL` y `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Prohibido referenciar variables con privilegios administrativos (`SUPABASE_SERVICE_ROLE_KEY`).
