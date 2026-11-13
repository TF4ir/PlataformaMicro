-- ==============================================================================
-- Migration: 20261109000000_profiles_privilege_hardening.sql
-- Description: Prevents self-service privilege escalation on public.profiles.
--
-- Justification:
--   The previous RLS policy `profiles_update_own` allowed a user to UPDATE any
--   column of their own row, including `role`, `tenant_id` and `student_code`.
--   Because FastAPI resolves authorization from `profiles.role`, a student
--   could turn themselves into a teacher/admin by updating that column.
--
-- Strategy (defense in depth):
--   1. Revoke table-level UPDATE from client roles and grant only editable
--      profile columns (full_name, avatar_url).
--   2. Add a trigger that rejects changes to identity/authorization columns
--      unless the actor is an admin/super_admin (or a trusted server role
--      without an auth.uid(), e.g. service_role / migrations).
-- ==============================================================================

-- 1. Column-level UPDATE privileges ------------------------------------------
REVOKE UPDATE ON public.profiles FROM authenticated;
REVOKE UPDATE ON public.profiles FROM anon;

GRANT UPDATE (full_name, avatar_url) ON public.profiles TO authenticated;

-- 2. Identity/authorization column guard -------------------------------------
CREATE OR REPLACE FUNCTION public.prevent_profile_privilege_escalation()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    actor_id UUID := auth.uid();
    actor_role public.user_role;
BEGIN
    IF NEW.id IS DISTINCT FROM OLD.id
       OR NEW.role IS DISTINCT FROM OLD.role
       OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.student_code IS DISTINCT FROM OLD.student_code THEN

        -- Trusted server-side operations (service_role, migrations, seeds)
        -- run without an end-user JWT and remain allowed.
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
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_profiles_prevent_privilege_escalation
    ON public.profiles;

CREATE TRIGGER trg_profiles_prevent_privilege_escalation
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.prevent_profile_privilege_escalation();

COMMENT ON FUNCTION public.prevent_profile_privilege_escalation() IS
    'Blocks self-service changes to profiles.role/tenant_id/student_code/id.';
