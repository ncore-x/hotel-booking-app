import { cn } from "../../lib/cn";
import type { HTMLAttributes } from "react";

export function Card({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-divider bg-card p-6",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
