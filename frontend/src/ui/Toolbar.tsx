import type { ReactNode } from "react";

/** Horizontal flex row used by inline composers (task/note/key-date/link). */
export function Toolbar({ wrap, children }: { wrap?: boolean; children: ReactNode }) {
  return (
    <div className={["toolbar", wrap ? "toolbar--wrap" : ""].filter(Boolean).join(" ")}>
      {children}
    </div>
  );
}
