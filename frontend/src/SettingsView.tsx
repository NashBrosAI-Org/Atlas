import { useEffect, useState } from "react";
import { getSettings, saveSettings, testConnection } from "./api";
import type { AppSettings, TestResult } from "./types";

export function SettingsView({ onSaved }: { onSaved?: () => void }) {
  const [s, setS] = useState<AppSettings | null>(null);
  const [password, setPassword] = useState("");
  const [test, setTest] = useState<TestResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    getSettings().then(setS).catch((e) => setMsg(String(e)));
  }, []);

  if (!s) return <div className="settings">Loading settings…</div>;

  const set = (patch: Partial<AppSettings>) => setS({ ...s, ...patch });

  async function save() {
    if (!s) return;
    setBusy(true);
    setMsg("");
    try {
      const snap = s;
      const saved = await saveSettings({
        use_fake: snap.use_fake,
        sn_instance_url: snap.sn_instance_url,
        sn_scope: snap.sn_scope,
        sn_oauth_username: snap.sn_oauth_username,
        ...(password ? { password } : {}),
      });
      setS(saved);
      setPassword("");
      setMsg("Saved.");
      onSaved?.();
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function runTest() {
    setBusy(true);
    setTest(null);
    try {
      setTest(await testConnection());
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="settings">
      <h2>Settings &amp; Integrations</h2>
      <p>
        Connect Atlas to your ServiceNow instance. Your password is stored in the macOS
        Keychain, never in a file. Tip: install the Atlas scoped app on your instance first.
      </p>

      <label>
        <input type="checkbox" checked={s.use_fake}
               onChange={(e) => set({ use_fake: e.target.checked })} />
        Try with demo data (no instance needed)
      </label>

      <fieldset disabled={s.use_fake}>
        <label>Instance URL
          <input value={s.sn_instance_url}
                 onChange={(e) => set({ sn_instance_url: e.target.value })}
                 placeholder="https://yourinstance.service-now.com" />
        </label>
        <label>Username
          <input value={s.sn_oauth_username}
                 onChange={(e) => set({ sn_oauth_username: e.target.value })} />
        </label>
        <label>Password
          <input type="password" value={password}
                 onChange={(e) => setPassword(e.target.value)}
                 placeholder={s.password_set ? "•••••••• (leave blank to keep)" : ""} />
        </label>
        <label>Scope
          <input value={s.sn_scope}
                 onChange={(e) => set({ sn_scope: e.target.value })} />
        </label>
      </fieldset>

      <div className="settings-actions">
        <button disabled={busy} onClick={save}>Save</button>
        <button disabled={busy || s.use_fake} onClick={runTest}>Test connection</button>
      </div>

      {msg && <p className="settings-msg">{msg}</p>}
      {test && (
        <p className={test.ok ? "ok" : "err"}>
          {test.ok ? "✓ Connection OK" : `✗ ${test.error ?? "Failed"}`}
        </p>
      )}
    </div>
  );
}
