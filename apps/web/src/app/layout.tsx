import type { Metadata } from "next";
import "./globals.css";
import { RoleProvider } from "@/lib/role-context";
import { AppShell } from "@/components/layout/app-shell";

export const metadata: Metadata = {
  title: "Nexo — Plataforma de Microaprendizaje Adaptativo",
  description:
    "Sistema web adaptativo para estudiantes de 5.° de secundaria. Repasos oportunos basados en retención y olvido.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="h-full">
      <body className="min-h-screen bg-[#f8fafc] font-sans antialiased text-slate-900">
        <RoleProvider>
          <AppShell>{children}</AppShell>
        </RoleProvider>
      </body>
    </html>
  );
}
