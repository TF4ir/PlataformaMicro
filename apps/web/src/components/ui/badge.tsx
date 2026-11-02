import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-wide transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-teal-100 text-teal-800",
        secondary:
          "border-transparent bg-slate-100 text-slate-800",
        outline:
          "text-slate-700 border border-slate-300",
        lavender:
          "border-transparent bg-[#f5f3ff] text-[#6d28d9] font-medium uppercase tracking-wider text-[11px]",
        success:
          "border-transparent bg-emerald-100 text-emerald-800",
        warning:
          "border-transparent bg-amber-100 text-amber-800",
        active:
          "border-transparent bg-emerald-100 text-emerald-700 font-medium",
        draft:
          "border-transparent bg-slate-100 text-slate-600 font-medium",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
