import { useState } from "react";
import { NowView } from "./NowView";
import { ClientsView } from "./ClientsView";
import { DossierView } from "./DossierView";

type View = "now" | "clients" | "dossier";

export default function App() {
  const [view, setView] = useState<View>("now");
  const [clientSysId, setClientSysId] = useState<string | null>(null);

  return (
    <div>
      <nav style={{ display: "flex", gap: 12, padding: "8px 16px", borderBottom: "1px solid #ddd", fontFamily: "system-ui" }}>
        <button onClick={() => setView("now")}>Now</button>
        <button onClick={() => setView("clients")}>Clients</button>
      </nav>
      {view === "now" && <NowView />}
      {view === "clients" && (
        <ClientsView onOpen={(id) => { setClientSysId(id); setView("dossier"); }} />
      )}
      {view === "dossier" && clientSysId && (
        <DossierView clientSysId={clientSysId} onBack={() => setView("clients")} />
      )}
    </div>
  );
}
