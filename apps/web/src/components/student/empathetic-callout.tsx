import React from "react";
import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmpatheticCalloutProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function EmpatheticCallout({
  title,
  children,
  className,
}: EmpatheticCalloutProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-2xl bg-[#f5f3ff] p-4 text-sm text-[#4c1d95] border border-[#ede9fe]",
        className
      )}
    >
      <div className="mt-0.5 flex-shrink-0 text-[#7c3aed]">
        <Sparkles className="h-5 w-5" />
      </div>
      <div className="space-y-1">
        {title && (
          <h4 className="font-semibold text-[#5b21b6]">{title}</h4>
        )}
        <div className="text-xs leading-relaxed text-[#5b21b6]/90">
          {children}
        </div>
      </div>
    </div>
  );
}
