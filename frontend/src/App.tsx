import { useEffect, useState } from "react";
import { NowView } from "./NowView";
import { ClientsView } from "./ClientsView";
import { DossierView } from "./DossierView";
import { SettingsView } from "./SettingsView";
import { HelpView } from "./HelpView";
import { AwarenessView } from "./AwarenessView";
import { SearchView } from "./SearchView";
import { getStatus } from "./api";

type View = "now" | "clients" | "dossier" | "settings" | "help" | "awareness" | "search";

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
        <button onClick={() => setView("awareness")}>Awareness</button>
        <button onClick={() => setView("search")}>Search</button>
        <button onClick={() => setView("settings")}>Settings</button>
        <button onClick={() => setView("help")}>Help</button>
      </nav>
      {view === "now" && <NowView />}
      {view === "clients" && (
        <ClientsView onOpen={(id) => { setClientSysId(id); setView("dossier"); }} />
      )}
      {view === "dossier" && clientSysId && (
        <DossierView clientSysId={clientSysId} onBack={() => setView("clients")} />
      )}
      {view === "awareness" && (
        <AwarenessView onOpenClient={(id) => { setClientSysId(id); setView("dossier"); }} />
      )}
      {view === "search" && (
        <SearchView onOpenClient={(id) => { setClientSysId(id); setView("dossier"); }} />
      )}
      {view === "settings" && (
        <SettingsView onSaved={() => setView("now")} />
      )}
      {view === "help" && <HelpView />}
    </div>
  );
}
