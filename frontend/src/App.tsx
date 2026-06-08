import { useEffect, useState } from "react";
import { NowView } from "./NowView";
import { ClientsView } from "./ClientsView";
import { DossierView } from "./DossierView";
import { SettingsView } from "./SettingsView";
import { HelpView } from "./HelpView";
import { AwarenessView } from "./AwarenessView";
import { SearchView } from "./SearchView";
import { AssociationsView } from "./AssociationsView";
import { QuickCapture } from "./QuickCapture";
import { Sidebar, type NavView } from "./Sidebar";
import { getStatus } from "./api";

type View = "now" | "clients" | "dossier" | "settings" | "help" | "awareness" | "search" | "associations";

export default function App() {
  const [view, setView] = useState<View>("now");
  const [clientSysId, setClientSysId] = useState<string | null>(null);
  const [statusChecked, setStatusChecked] = useState(false);
  const [capturing, setCapturing] = useState(false);

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

  // Dossier is reached via Clients, so highlight Clients while it's open.
  const activeNav: NavView = view === "dossier" ? "clients" : view;

  return (
    <div className="app-shell">
      <Sidebar
        current={activeNav}
        onNavigate={(v) => setView(v)}
        onCapture={() => setCapturing(true)}
      />
      <main className="app-main">
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
        {view === "associations" && (
          <AssociationsView onOpenClient={(id) => { setClientSysId(id); setView("dossier"); }} />
        )}
        {view === "settings" && (
          <SettingsView onSaved={() => setView("now")} />
        )}
        {view === "help" && <HelpView />}
      </main>
      {capturing && <QuickCapture onClose={() => setCapturing(false)} />}
    </div>
  );
}
