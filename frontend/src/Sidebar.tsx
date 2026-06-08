import { Button } from "./ui";

export type NavView =
  | "now" | "clients" | "awareness" | "search" | "associations" | "settings" | "help";

const PRIMARY: { id: NavView; label: string }[] = [
  { id: "now", label: "Now" },
  { id: "clients", label: "Clients" },
  { id: "awareness", label: "Awareness" },
  { id: "search", label: "Search" },
  { id: "associations", label: "Associations" },
];

const FOOTER: { id: NavView; label: string }[] = [
  { id: "settings", label: "Settings" },
  { id: "help", label: "Help" },
];

/** Persistent left navigation rail (replaces the old top <nav>). */
export function Sidebar(
  { current, onNavigate, onCapture }:
    { current: NavView; onNavigate: (v: NavView) => void; onCapture: () => void },
) {
  const item = ({ id, label }: { id: NavView; label: string }) => (
    <button
      key={id}
      className={`sidebar__item${current === id ? " sidebar__item--active" : ""}`}
      aria-current={current === id ? "page" : undefined}
      onClick={() => onNavigate(id)}
    >
      {label}
    </button>
  );

  return (
    <aside className="app-sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__mark" aria-hidden="true" />
        Atlas
      </div>

      <div className="sidebar__capture">
        <Button variant="primary" onClick={onCapture} style={{ width: "100%" }}>
          ＋ Capture
        </Button>
      </div>

      <nav className="sidebar__nav" aria-label="Primary">
        {PRIMARY.map(item)}
      </nav>

      <div className="sidebar__footer">
        <nav className="sidebar__nav" aria-label="Settings and help">
          {FOOTER.map(item)}
        </nav>
      </div>
    </aside>
  );
}
