-- ==============================================================================
-- Migration: 20261109010000_release_mvp_security_hardening.sql
-- Description: Release MVP security consolidation.
--
-- Fixes:
--   F-01: Removes the `sections` <-> `enrollments` RLS recursion by replacing
--         the recursive `sections_select_all` policy with a SECURITY DEFINER
--         helper scoped to the caller's own enrollments.
--   F-04: Stops exposing every profile of the tenant. A user can read their own
--         profile, teachers can read profiles of students in their sections,
--         and admins can read their tenant (super_admins: all tenants).
--   F-05: Revokes unnecessary table-level privileges on `profiles` from the
--         client roles (INSERT/DELETE/TRUNCATE/REFERENCES/TRIGGER).
--   F-06: Makes the privilege-escalation trigger fail closed for PostgREST
--         `anon`/`authenticated` sessions that lack an `auth.uid()`.
--
-- This migration is incremental. Historical migrations are not modified.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- F-01: Break the RLS recursion without granting blanket section access.
--
-- `sections_select_all` referenced `enrollments`, while
-- `enrollments_select_policy` referenced `sections`, producing an infinite
-- recursion. The helper below is SECURITY DEFINER and therefore evaluates the
-- enrollment lookup without re-entering RLS.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.is_enrolled_in_section(p_section_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.enrollments e
        WHERE e.section_id = p_section_id
          AND e.student_id = (SELECT auth.uid())
    );
$$;

COMMENT ON FUNCTION public.is_enrolled_in_section(UUID) IS
    'True when the current user is enrolled in the given section. SECURITY DEFINER avoids RLS recursion between sections and enrollments.';

DROP POLICY IF EXISTS "sections_select_all" ON public.sections;
DROP POLICY IF EXISTS "sections_select_tenant" ON public.sections;
DROP POLICY IF EXISTS "sections_select_scoped" ON public.sections;

CREATE POLICY "sections_select_scoped" ON public.sections
    FOR SELECT USING (
        teacher_id = (SELECT auth.uid())
        OR public.is_enrolled_in_section(sections.id)
        OR (SELECT public.current_user_role()) = 'super_admin'
        OR (
            tenant_id = (SELECT public.current_user_tenant_id())
            AND (SELECT public.current_user_role()) = 'admin'
        )
    );

COMMENT ON POLICY "sections_select_scoped" ON public.sections IS
    'The assigned teacher, enrolled students, and tenant admins can read a section. Super admins can read all. No blanket/tenant-wide section access for students.';

-- ------------------------------------------------------------------------------
-- F-04: Least-privilege profile reads.
--
-- The previous policy exposed every profile in the tenant to every student.
-- The teacher roster continues to work because `is_teacher_of_student` is
-- SECURITY DEFINER and covers exactly the students assigned to the teacher.
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "profiles_select_own_or_same_tenant" ON public.profiles;

DROP POLICY IF EXISTS "profiles_select_own" ON public.profiles;
CREATE POLICY "profiles_select_own" ON public.profiles
    FOR SELECT USING (id = (SELECT auth.uid()));

DROP POLICY IF EXISTS "profiles_select_teacher_students" ON public.profiles;
CREATE POLICY "profiles_select_teacher_students" ON public.profiles
    FOR SELECT USING (public.is_teacher_of_student(id));

DROP POLICY IF EXISTS "profiles_select_admin_scope" ON public.profiles;
CREATE POLICY "profiles_select_admin_scope" ON public.profiles
    FOR SELECT USING (
        (SELECT public.current_user_role()) = 'super_admin'
        OR (
            tenant_id = (SELECT public.current_user_tenant_id())
            AND (SELECT public.current_user_role()) = 'admin'
        )
    );

COMMENT ON POLICY "profiles_select_own" ON public.profiles IS
    'A user can always read their own profile.';
COMMENT ON POLICY "profiles_select_teacher_students" ON public.profiles IS
    'Teachers can read profiles of students enrolled in their sections only.';
COMMENT ON POLICY "profiles_select_admin_scope" ON public.profiles IS
    'Admins can read profiles in their tenant; super_admins can read all tenants.';

-- ------------------------------------------------------------------------------
-- F-05: Remove unnecessary table-level privileges from client roles.
--
-- `profiles` is read through RLS and updated only through the column-level
-- grants on full_name/avatar_url established by 20261109000000. INSERT and
-- DELETE have no policies, and TRUNCATE is not protected by RLS.
-- ------------------------------------------------------------------------------
REVOKE UPDATE ON public.profiles FROM anon, authenticated;
REVOKE INSERT, DELETE, TRUNCATE, REFERENCES, TRIGGER
    ON public.profiles FROM anon, authenticated;
REVOKE INSERT, DELETE, TRUNCATE, REFERENCES, TRIGGER
    ON public.profiles FROM PUBLIC;

-- Keep the legitimate self-service columns available to authenticated users.
GRANT UPDATE (full_name, avatar_url) ON public.profiles TO authenticated;

-- ------------------------------------------------------------------------------
-- F-06: Fail closed when a PostgREST client session has no auth.uid().
--
-- Trusted server operations (service_role, migrations, seeds, direct SQL)
-- continue to work. A PostgREST `anon`/`authenticated` session without a
-- subject cannot change identity/authorization columns.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.prevent_profile_privilege_escalation()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    actor_id UUID := auth.uid();
    actor_role public.user_role;
    request_role TEXT := COALESCE(auth.role(), '');
BEGIN
    IF NEW.id IS DISTINCT FROM OLD.id
       OR NEW.role IS DISTINCT FROM OLD.role
       OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.student_code IS DISTINCT FROM OLD.student_code THEN

        IF actor_id IS NOT NULL THEN
            SELECT role INTO actor_role
            FROM public.profiles
            WHERE id = actor_id;

            IF actor_role IS NULL
               OR actor_role NOT IN ('super_admin', 'admin') THEN
                RAISE EXCEPTION
                    'profiles: role, tenant_id, student_code and id are immutable for non-admin users'
                    USING ERRCODE = '42501';
            END IF;

        ELSIF request_role IN ('anon', 'authenticated') THEN
            -- A client-facing PostgREST session without a verified subject must
            -- never be able to mutate identity/authorization columns.
            RAISE EXCEPTION
                'profiles: role, tenant_id, student_code and id are immutable for client sessions without a verified user'
                USING ERRCODE = '42501';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.prevent_profile_privilege_escalation() IS
    'Blocks self-service changes to profiles.role/tenant_id/student_code/id, including client sessions without auth.uid().';
