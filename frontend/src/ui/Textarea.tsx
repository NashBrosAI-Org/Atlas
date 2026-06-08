import type { TextareaHTMLAttributes } from "react";

export function Textarea(
  { invalid, className = "", ...rest }:
    TextareaHTMLAttributes<HTMLTextAreaElement> & { invalid?: boolean },
) {
  const cls = ["textarea", invalid ? "textarea--invalid" : "", className]
    .filter(Boolean).join(" ");
  return <textarea className={cls} {...rest} />;
}
