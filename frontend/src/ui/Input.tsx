import type { InputHTMLAttributes } from "react";

/** Native <input> with shared styling. `type` passes through (date/number/password). */
export function Input(
  { invalid, className = "", ...rest }:
    InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean },
) {
  const cls = ["input", invalid ? "input--invalid" : "", className]
    .filter(Boolean).join(" ");
  return <input className={cls} {...rest} />;
}
