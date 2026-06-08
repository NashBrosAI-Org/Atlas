import type { InputHTMLAttributes, ReactNode } from "react";

/** Label-wrapped checkbox. The label text follows the box. */
export function Checkbox(
  { label, className = "", ...rest }:
    InputHTMLAttributes<HTMLInputElement> & { label?: ReactNode },
) {
  return (
    <label className={["checkbox", className].filter(Boolean).join(" ")}>
      <input type="checkbox" {...rest} />
      {label}
    </label>
  );
}
