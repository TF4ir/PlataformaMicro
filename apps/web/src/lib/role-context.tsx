"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { UserRole } from "@/types/ui";
import { useRouter, usePathname } from "next/navigation";
import { mockStudent, mockTeacher } from "@/lib/mock-data";

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
  login: (
    role: UserRole,
    user?: Partial<AuthUser>,
    redirectTo?: string
  ) => void;
  logout: () => Promise<void>;
  setRole: (role: UserRole) => void;
  toggleRole: () => void;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

// Helper to get cookie value on client
function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

// Helper to set cookie on client
function setCookie(name: string, value: string, days: number = 7) {
  if (typeof document === "undefined") return;
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

// Helper to erase cookie on client
function eraseCookie(name: string) {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=; Max-Age=0; path=/; SameSite=Lax`;
}

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const [role, setRoleState] = useState<UserRole>("student");
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);

  const router = useRouter();
  const pathname = usePathname();

  // Initialize auth state from Supabase Auth & cookies
  useEffect(() => {
    let isMounted = true;
    async function syncSession() {
      try {
        const { createClient } = await import("@/lib/supabase/client");
        const supabase = createClient();
        const { data: { session }, error } = await supabase.auth.getSession();
        if (!isMounted) return;

        if (!error && session?.user) {
          setIsAuthenticated(true);
          const meta = session.user.user_metadata || {};
          const userRole = (meta.role as UserRole) || (getCookie("nexo_role") as UserRole) || "student";
          setRoleState(userRole);
          setCurrentUser({
            id: session.user.id,
            name: meta.full_name || getCookie("nexo_user_name") || session.user.email?.split("@")[0] || "Usuario",
            email: session.user.email || "",
            role: userRole,
            code: meta.student_code || (userRole === "teacher" ? "DOC-101" : "EST-501"),
          });
          setCookie("nexo_role", userRole, 7);
          return;
        }
      } catch (e) {
        // Continue to cookie fallback
      }

      const savedRole = (getCookie("nexo_role") as UserRole) || null;
      const sessionToken = getCookie("nexo_session");

      if (sessionToken && savedRole) {
        setIsAuthenticated(true);
        setRoleState(savedRole);
        const savedName = getCookie("nexo_user_name");
        setCurrentUser({
          id: savedRole === "teacher" ? "d0000000-0000-0000-0000-000000000001" : "e0000000-0000-0000-0000-000000000001",
          name: savedName || (savedRole === "teacher" ? "Ana García" : "Lucía Mendoza"),
          email: savedRole === "teacher" ? "ana.garcia@nexo.edu.pe" : "lucia.mendoza@nexo.edu.pe",
          role: savedRole,
          code: savedRole === "teacher" ? "DOC-101" : "EST-501",
        });
      } else {
        const isPublicPath =
          pathname === "/login" || pathname === "/recovery" || pathname === "/";
        if (!isPublicPath) {
          setIsAuthenticated(false);
        }
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

  const login = (
    newRole: UserRole,
    user?: Partial<AuthUser>,
    redirectTo?: string
  ) => {
    setIsAuthenticated(true);
    setRoleState(newRole);

    const fullUser: AuthUser = {
      id: user?.id || (newRole === "teacher" ? "d0000000-0000-0000-0000-000000000001" : "e0000000-0000-0000-0000-000000000001"),
      name:
        user?.name || (newRole === "teacher" ? "Ana García" : "Lucía Mendoza"),
      email:
        user?.email ||
        (newRole === "teacher"
          ? "ana.garcia@nexo.edu.pe"
          : "lucia.mendoza@nexo.edu.pe"),
      role: newRole,
      code: user?.code || (newRole === "teacher" ? "DOC-101" : "EST-501"),
    };

    setCurrentUser(fullUser);
    setCookie("nexo_session", "session_active_" + Date.now(), 7);
    setCookie("nexo_role", newRole, 7);
    setCookie("nexo_user_name", fullUser.name, 7);

    // Validate redirect target against role privileges
    if (redirectTo && redirectTo.startsWith("/")) {
      if (newRole === "student" && !redirectTo.startsWith("/teacher")) {
        router.push(redirectTo);
        return;
      }
      if (newRole === "teacher" && redirectTo.startsWith("/teacher")) {
        router.push(redirectTo);
        return;
      }
    }

    if (newRole === "teacher") {
      router.push("/teacher/dashboard");
    } else {
      router.push("/dashboard");
    }
  };

  const logout = async () => {
    try {
      const { createClient } = await import("@/lib/supabase/client");
      const supabase = createClient();
      await supabase.auth.signOut();
    } catch (e) {
      // ignore
    }

    eraseCookie("nexo_session");
    eraseCookie("nexo_role");
    eraseCookie("nexo_user_name");

    setIsAuthenticated(false);
    setCurrentUser(null);
    router.push("/login");
  };

  const setRole = (newRole: UserRole) => {
    setRoleState(newRole);
    setCookie("nexo_role", newRole, 7);
    if (newRole === "teacher") {
      router.push("/teacher/dashboard");
    } else {
      router.push("/dashboard");
    }
  };

  const toggleRole = () => {
    const nextRole = role === "student" ? "teacher" : "student";
    setRole(nextRole);
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
        setRole,
        toggleRole,
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
