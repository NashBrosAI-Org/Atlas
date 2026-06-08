import type { ReactNode } from "react";
import { InfoHint } from "../InfoHint";

/** Label + control + optional InfoHint / help / error wrapper. */
export function Field(
  { label, hint, help, error, children }:
    { label?: ReactNode; hint?: string; help?: ReactNode; error?: ReactNode; children: ReactNode },
) {
  return (
    <label className="field">
      {label != null && (
        <span className="field__label">
          {label}
          {hint && <InfoHint text={hint} />}
        </span>
      )}
      {children}
      {help && <span className="field__help">{help}</span>}
      {error && <span className="field__error">{error}</span>}
    </label>
  );
}
