-- ==============================================================================
-- Migration: 20261106000000_fix_rls_select_policies.sql
-- Description: Adds missing SELECT policies for RLS-enabled tables:
--              sections, tenants, student_knowledge_states, student_metrics, review_assignments.
-- ==============================================================================

-- 1. sections (Allows users within the same tenant or enrolled students/assigned teachers to view sections)
DO $$ BEGIN
    CREATE POLICY "sections_select_all" ON public.sections
        FOR SELECT USING (
            tenant_id = (SELECT public.current_user_tenant_id())
            OR teacher_id = (SELECT auth.uid())
            OR EXISTS (
                SELECT 1 FROM public.enrollments e
                WHERE e.section_id = sections.id AND e.student_id = (SELECT auth.uid())
            )
            OR (SELECT public.current_user_role()) IN ('super_admin', 'admin')
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- 2. tenants (Allows users within the tenant to read basic tenant info)
DO $$ BEGIN
    CREATE POLICY "tenants_select_own" ON public.tenants
        FOR SELECT USING (
            id = (SELECT public.current_user_tenant_id())
            OR (SELECT public.current_user_role()) IN ('super_admin', 'admin')
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- 3. student_knowledge_states (Student can read own, teacher can read assigned students)
DO $$ BEGIN
    CREATE POLICY "student_knowledge_states_select" ON public.student_knowledge_states
        FOR SELECT USING (
            student_id = (SELECT auth.uid()) 
            OR (SELECT public.is_teacher_of_student(student_id)) 
            OR (SELECT public.current_user_role()) IN ('super_admin', 'admin')
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- 4. student_metrics (Student can read own, teacher can read assigned students)
DO $$ BEGIN
    CREATE POLICY "student_metrics_select" ON public.student_metrics
        FOR SELECT USING (
            student_id = (SELECT auth.uid()) 
            OR (SELECT public.is_teacher_of_student(student_id)) 
            OR (SELECT public.current_user_role()) IN ('super_admin', 'admin')
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- 5. review_assignments (Student can read own, teacher can read assigned students)
DO $$ BEGIN
    CREATE POLICY "review_assignments_select" ON public.review_assignments
        FOR SELECT USING (
            student_id = (SELECT auth.uid()) 
            OR (SELECT public.is_teacher_of_student(student_id)) 
            OR (SELECT public.current_user_role()) IN ('super_admin', 'admin')
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;
