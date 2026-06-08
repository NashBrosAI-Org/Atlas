import type { ReactNode } from "react";

type Tone = "neutral" | "success" | "danger" | "warning" | "info" | "accent";

/** Compact status/label chip. Pass `onRemove` to render a × (used for tags). */
export function Badge(
  { tone = "neutral", pill, children, onRemove, removeLabel }:
    { tone?: Tone; pill?: boolean; children: ReactNode; onRemove?: () => void; removeLabel?: string },
) {
  const cls = [
    "badge",
    tone !== "neutral" ? `badge--${tone}` : "",
    pill ? "badge--pill" : "",
  ].filter(Boolean).join(" ");
  return (
    <span className={cls}>
      {children}
      {onRemove && (
        <button type="button" className="badge__remove"
          aria-label={removeLabel ?? "Remove"} onClick={onRemove}>×</button>
      )}
    </span>
  );
}
