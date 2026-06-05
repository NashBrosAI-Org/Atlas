/** A small ⓘ affordance that explains a field/section on hover & to screen readers.
 *  Native title for hover + aria-label for a11y; no dependencies. */
export function InfoHint({ text }: { text: string }) {
  return (
    <span role="img" aria-label={text} title={text}
      style={{ display: "inline-block", marginLeft: 4, width: 14, height: 14, lineHeight: "14px",
        textAlign: "center", fontSize: 10, color: "#fff", background: "#9aa", borderRadius: "50%",
        cursor: "help", userSelect: "none", verticalAlign: "middle" }}>i</span>
  );
}
