"use client";

import * as React from "react";
import { Dialog as SheetPrimitive } from "radix-ui";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export const Sheet = SheetPrimitive.Root;
export const SheetTrigger = SheetPrimitive.Trigger;
export const SheetClose = SheetPrimitive.Close;

export function SheetContent({
  className,
  children,
  side = "right",
  ...props
}: React.ComponentProps<typeof SheetPrimitive.Content> & { side?: "right" | "bottom" | "left" }) {
  return (
    <SheetPrimitive.Portal>
      <SheetPrimitive.Overlay className="fixed inset-0 z-50 bg-ink/15 backdrop-blur-[2px] data-open:animate-in data-open:fade-in-0 data-closed:animate-out data-closed:fade-out-0" />
      <SheetPrimitive.Content
        className={cn(
          "fixed z-50 flex flex-col bg-paper shadow-float outline-none duration-300 ease-out",
          side === "right" &&
            "inset-y-2 right-2 w-[calc(100%-16px)] max-w-[460px] rounded-3xl data-open:animate-in data-open:slide-in-from-right-12 data-open:fade-in-0 data-closed:animate-out data-closed:slide-out-to-right-12 data-closed:fade-out-0",
          side === "left" &&
            "inset-y-2 left-2 w-[calc(100%-16px)] max-w-[420px] rounded-3xl data-open:animate-in data-open:slide-in-from-left-12 data-closed:animate-out data-closed:slide-out-to-left-12",
          side === "bottom" &&
            "inset-x-2 bottom-2 max-h-[85dvh] rounded-3xl data-open:animate-in data-open:slide-in-from-bottom-12 data-closed:animate-out data-closed:slide-out-to-bottom-12",
          className,
        )}
        {...props}
      >
        {children}
        <SheetPrimitive.Close
          className="absolute top-4 right-4 grid size-9 place-items-center rounded-full bg-white text-body shadow-card transition hover:text-ink"
          aria-label="Close"
        >
          <X className="size-4" />
        </SheetPrimitive.Close>
      </SheetPrimitive.Content>
    </SheetPrimitive.Portal>
  );
}

export function SheetHeader({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("flex flex-col gap-1 px-6 pt-6 pb-4 pr-16", className)} {...props} />;
}

export function SheetTitle({ className, ...props }: React.ComponentProps<typeof SheetPrimitive.Title>) {
  return <SheetPrimitive.Title className={cn("text-[22px] font-semibold tracking-[-0.03em] text-ink", className)} {...props} />;
}

export function SheetDescription({ className, ...props }: React.ComponentProps<typeof SheetPrimitive.Description>) {
  return <SheetPrimitive.Description className={cn("text-sm text-muted", className)} {...props} />;
}
