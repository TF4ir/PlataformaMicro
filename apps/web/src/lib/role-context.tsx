"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { UserRole } from "@/types/ui";
import { useRouter, usePathname } from "next/navigation";
import {
  normalizeRole,
  portalRoleFor,
  safeRedirectForRole,
} from "@/lib/auth/authorization";

interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  code?: string;
}

interface RoleContextType {
  role: UserRole;
  isAuthenticated: boolean;
  currentUser: AuthUser | null;
  isMobileMenuOpen: boolean;
  setIsMobileMenuOpen: (open: boolean) => void;
  toggleMobileMenu: () => void;
  login: (user: AuthUser, redirectTo?: string) => void;
  logout: () => Promise<void>;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

const LEGACY_AUTH_COOKIES = [
  "nexo_session",
  "nexo_role",
  "nexo_user_name",
] as const;

/**
 * Removes cookies written by the previous client-side auth simulation.
 * They are no longer read anywhere; deleting them prevents stale values from
 * confusing users or future code.
 */
function clearLegacyAuthCookies() {
  if (typeof document === "undefined") return;
  for (const name of LEGACY_AUTH_COOKIES) {
    document.cookie = `${name}=; Max-Age=0; path=/; SameSite=Lax`;
  }
}

interface VerifiedProfile {
  role: UserRole;
  name: string;
  email: string;
  code?: string;
  id: string;
}

/**
 * Loads the signed-in user from Supabase Auth and the authoritative role from
 * `public.profiles`. Returns `null` when there is no verified session.
 */
async function loadVerifiedProfile(): Promise<VerifiedProfile | null> {
  const { createClient } = await import("@/lib/supabase/client");
  const supabase = createClient();

  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();
  if (userError || !user) return null;

  const { data: profile, error: profileError } = await supabase
    .from("profiles")
    .select("role, full_name, student_code")
    .eq("id", user.id)
    .maybeSingle();
  if (profileError || !profile) return null;

  const verifiedRole = normalizeRole(profile.role);
  const portalRole = portalRoleFor(verifiedRole);
  if (!verifiedRole || !portalRole) return null;

  return {
    id: user.id,
    name:
      profile.full_name ||
      user.email?.split("@")[0] ||
      "Usuario",
    email: user.email || "",
    role: portalRole,
    code:
      typeof profile.student_code === "string"
        ? profile.student_code
        : undefined,
  };
}

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const [role, setRoleState] = useState<UserRole>("student");
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);

  const router = useRouter();
  const pathname = usePathname();

  // Initialize auth state from the verified Supabase session only.
  useEffect(() => {
    let isMounted = true;
    clearLegacyAuthCookies();

    async function syncSession() {
      try {
        const profile = await loadVerifiedProfile();
        if (!isMounted) return;

        if (!profile) {
          setIsAuthenticated(false);
          setCurrentUser(null);
          return;
        }

        setIsAuthenticated(true);
        setRoleState(profile.role);
        setCurrentUser({
          id: profile.id,
          name: profile.name,
          email: profile.email,
          role: profile.role,
          code: profile.code,
        });
      } catch {
        if (!isMounted) return;
        setIsAuthenticated(false);
        setCurrentUser(null);
      }
    }

    syncSession();
    return () => {
      isMounted = false;
    };
  }, [pathname]);

  // Close mobile sidebar on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  const login = (user: AuthUser, redirectTo?: string) => {
    setIsAuthenticated(true);
    setRoleState(user.role);
    setCurrentUser(user);

    const verifiedRole = normalizeRole(user.role);
    router.push(safeRedirectForRole(verifiedRole, redirectTo));
  };

  const logout = async () => {
    try {
      const { createClient } = await import("@/lib/supabase/client");
      const supabase = createClient();
      await supabase.auth.signOut();
    } catch {
      // The local state is cleared even if the network sign-out fails.
    }

    clearLegacyAuthCookies();
    setIsAuthenticated(false);
    setCurrentUser(null);
    router.push("/login");
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen((prev) => !prev);
  };

  return (
    <RoleContext.Provider
      value={{
        role,
        isAuthenticated,
        currentUser,
        isMobileMenuOpen,
        setIsMobileMenuOpen,
        toggleMobileMenu,
        login,
        logout,
      }}
    >
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  const context = useContext(RoleContext);
  if (!context) {
    throw new Error("useRole must be used within a RoleProvider");
  }
  return context;
}
