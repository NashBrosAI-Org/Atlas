import type { HTMLAttributes, ReactNode } from "react";

export function Card(
  { variant, className = "", children, ...rest }:
    HTMLAttributes<HTMLDivElement> & { variant?: "muted" | "accent" | "warning"; children: ReactNode },
) {
  const cls = ["card", variant ? `card--${variant}` : "", className]
    .filter(Boolean).join(" ");
  return <div className={cls} {...rest}>{children}</div>;
}
