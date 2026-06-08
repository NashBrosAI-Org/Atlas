import type { SelectHTMLAttributes } from "react";

/** Native <select> — kept native so option values/display stay testable
 *  (AssociationsView.test queries by display value). */
export function Select(
  { className = "", children, ...rest }: SelectHTMLAttributes<HTMLSelectElement>,
) {
  return (
    <select className={["select", className].filter(Boolean).join(" ")} {...rest}>
      {children}
    </select>
  );
}
