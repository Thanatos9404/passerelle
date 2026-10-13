"use client";

import * as React from "react";
import { Tabs as TabsPrimitive } from "radix-ui";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";

export const Tabs = TabsPrimitive.Root;
export const TabsContent = TabsPrimitive.Content;

/**
 * Pill tab list with a shared-layout indicator (motion `layoutId`) that glides between triggers.
 * `id` must be unique per tab list on the page.
 */
export function PillTabs<T extends string>({
  id,
  value,
  items,
  className,
  size = "md",
}: {
  id: string;
  value: T;
  items: { value: T; label: React.ReactNode; icon?: React.ReactNode; disabled?: boolean }[];
  className?: string;
  size?: "sm" | "md";
}) {
  return (
    <TabsPrimitive.List className={cn("relative inline-flex items-center gap-0.5 rounded-pill bg-sand-2 p-1", className)}>
      {items.map((it) => {
        const active = it.value === value;
        return (
          <TabsPrimitive.Trigger
            key={it.value}
            value={it.value}
            disabled={it.disabled}
            className={cn(
              "relative inline-flex items-center gap-1.5 rounded-pill font-medium whitespace-nowrap transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ink/40 disabled:opacity-40",
              size === "sm" ? "h-8 px-3 text-[13px]" : "h-9 px-4 text-[14px]",
              active ? "text-ink" : "text-muted hover:text-ink",
            )}
          >
            {active && (
              <motion.span
                layoutId={`pill-${id}`}
                className="absolute inset-0 rounded-pill bg-white shadow-card"
                transition={{ type: "spring", stiffness: 420, damping: 34 }}
              />
            )}
            <span className="relative z-10 inline-flex items-center gap-1.5">
              {it.icon}
              {it.label}
            </span>
          </TabsPrimitive.Trigger>
        );
      })}
    </TabsPrimitive.List>
  );
}
