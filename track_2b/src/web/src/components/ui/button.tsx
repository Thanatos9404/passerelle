"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  "group/btn relative inline-flex items-center justify-center gap-2 rounded-pill font-semibold whitespace-nowrap transition-[transform,background-color,box-shadow,color] duration-300 ease-[cubic-bezier(.22,1,.36,1)] outline-none focus-visible:ring-2 focus-visible:ring-ink/40 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-45 active:scale-[0.98]",
  {
    variants: {
      variant: {
        primary: "bg-ink text-white shadow-pill hover:-translate-y-0.5 hover:bg-[#2a2422]",
        secondary: "frost border border-white/70 text-ink shadow-[0_1px_2px_rgba(97,74,68,.08)] hover:-translate-y-0.5 hover:bg-white",
        outline: "border border-line-strong bg-white text-ink hover:-translate-y-0.5 hover:border-ink/25",
        ghost: "text-body hover:bg-sand-2 hover:text-ink",
        soft: "bg-sand-2 text-ink hover:bg-sand",
      },
      size: {
        lg: "h-14 px-7 text-[16px]",
        md: "h-11 px-5 text-[15px]",
        sm: "h-9 px-4 text-[13.5px]",
        icon: "size-9",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

type Common = VariantProps<typeof buttonVariants> & { arrow?: boolean; className?: string; children?: React.ReactNode };

export function Button({ variant, size, arrow, className, children, ...props }: Common & React.ComponentProps<"button">) {
  return (
    <button className={cn(buttonVariants({ variant, size }), className)} {...props}>
      {children}
      {arrow && <ArrowRight className="size-4 transition-transform duration-300 group-hover/btn:translate-x-0.5" aria-hidden />}
    </button>
  );
}

export function ButtonLink({ variant, size, arrow, className, children, href, ...props }: Common & React.ComponentProps<typeof Link>) {
  return (
    <Link href={href} className={cn(buttonVariants({ variant, size }), className)} {...props}>
      {children}
      {arrow && <ArrowRight className="size-4 transition-transform duration-300 group-hover/btn:translate-x-0.5" aria-hidden />}
    </Link>
  );
}
