import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

/** Accessible modal dialog: backdrop click-close, Escape-to-close, focus-on-open,
 *  role="dialog"/aria-modal. Extracted from MeetingPrepPanel's a11y pattern. */
export function Modal(
  { title, onClose, width, children }:
    { title: string; onClose: () => void; width?: number; children: ReactNode },
) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    closeRef.current?.focus();
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title}
        style={width ? { maxWidth: width } : undefined}
        onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2 className="modal__title">{title}</h2>
          <button ref={closeRef} className="btn btn--sm" onClick={onClose}>Close</button>
        </div>
        <div className="modal__body">{children}</div>
      </div>
    </div>
  );
}
