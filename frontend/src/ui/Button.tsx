import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "icon";

/** Native <button> with design-system variants. Children are the label, so
 *  accessible names stay intact (tests query by name). */
export function Button(
  { variant = "secondary", size, className = "", ...rest }:
    ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: "sm" },
) {
  const cls = [
    "btn",
    variant !== "secondary" ? `btn--${variant}` : "",
    size === "sm" ? "btn--sm" : "",
    className,
  ].filter(Boolean).join(" ");
  return <button type="button" className={cls} {...rest} />;
}
