import { useEffect, useState } from "react";
import { NowView } from "./NowView";
import { ClientsView } from "./ClientsView";
import { DossierView } from "./DossierView";
import { SettingsView } from "./SettingsView";
import { getStatus } from "./api";

type View = "now" | "clients" | "dossier" | "settings";

export default function App() {
  const [view, setView] = useState<View>("now");
  const [clientSysId, setClientSysId] = useState<string | null>(null);
  const [statusChecked, setStatusChecked] = useState(false);

  // First-run: if not configured and not in demo mode, open Settings immediately.
  useEffect(() => {
    getStatus()
      .then(({ fake, configured }) => {
        if (!configured && !fake) setView("settings");
      })
      .catch(() => {
        // Backend unreachable — stay on Now; user can navigate to Settings manually.
      })
      .finally(() => setStatusChecked(true));
  }, []);

  // Don't render the main UI until we know which view to start on, to avoid a flash.
  if (!statusChecked) return null;

  return (
    <div>
      <nav style={{ display: "flex", gap: 12, padding: "8px 16px", borderBottom: "1px solid #ddd", fontFamily: "system-ui" }}>
        <button onClick={() => setView("now")}>Now</button>
        <button onClick={() => setView("clients")}>Clients</button>
        <button onClick={() => setView("settings")}>Settings</button>
      </nav>
      {view === "now" && <NowView />}
      {view === "clients" && (
        <ClientsView onOpen={(id) => { setClientSysId(id); setView("dossier"); }} />
      )}
      {view === "dossier" && clientSysId && (
        <DossierView clientSysId={clientSysId} onBack={() => setView("clients")} />
      )}
      {view === "settings" && (
        <SettingsView onSaved={() => setView("now")} />
      )}
    </div>
  );
}
