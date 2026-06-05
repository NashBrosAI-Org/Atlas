import { useEffect, useState } from "react";
import { getSettings, saveSettings, testConnection, getBackupStatus, runExport, restoreBackup } from "./api";
import type { AppSettings, TestResult, BackupStatus } from "./types";

export function SettingsView({ onSaved }: { onSaved?: () => void }) {
  const [s, setS] = useState<AppSettings | null>(null);
  const [password, setPassword] = useState("");
  const [test, setTest] = useState<TestResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [bk, setBk] = useState<BackupStatus | null>(null);
  const [bkMsg, setBkMsg] = useState("");

  useEffect(() => {
    getSettings().then(setS).catch((e) => setMsg(String(e)));
    getBackupStatus().then(setBk).catch(() => {});
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
        cooling_days: snap.cooling_days,
        stale_days: snap.stale_days,
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
    } catch (e) {
      setTest({ ok: false, error: String(e) });
    } finally {
      setBusy(false);
    }
  }

  async function restoreNow() {
    if (!window.confirm("Restore the latest backup? This upserts records by sys_id into the current instance.")) return;
    setBusy(true);
    setBkMsg("");
    try {
      const r = await restoreBackup();
      setBkMsg(`Restored from ${r.from}: ${r.created} created, ${r.updated} updated.`);
      setBk(await getBackupStatus());
    } catch (e) {
      setBkMsg(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function exportNow() {
    setBusy(true);
    setBkMsg("");
    try {
      const r = await runExport();
      const total = Object.values(r.counts).reduce((a, b) => a + b, 0);
      setBkMsg(`Exported ${total} record(s) → ${r.path}`);
      setBk(await getBackupStatus());
    } catch (e) {
      setBkMsg(String(e));
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

      <fieldset>
        <legend>Radar thresholds (days)</legend>
        <label>Cooling after
          <input type="number" min={1} value={s.cooling_days}
                 onChange={(e) => set({ cooling_days: Number(e.target.value) })} />
        </label>
        <label>Stale after
          <input type="number" min={1} value={s.stale_days}
                 onChange={(e) => set({ stale_days: Number(e.target.value) })} />
        </label>
      </fieldset>

      <fieldset>
        <legend>Backup</legend>
        <p>
          Export every record to a JSON snapshot. The ServiceNow instance is not a durable
          archive — keep an off-instance copy. Atlas also backs up on launch when the last
          one is older than {bk?.max_age_days ?? 7} days.
        </p>
        <p className={bk?.stale ? "err" : "ok"}>
          {bk
            ? bk.last_backup
              ? `Last backup: ${new Date(bk.last_backup).toLocaleString()} (${bk.count} total)${bk.stale ? " — overdue" : ""}`
              : "No backups yet"
            : "…"}
        </p>
        <button disabled={busy} onClick={exportNow}>Export now</button>
        <button disabled={busy || !bk?.last_backup} onClick={restoreNow} style={{ marginLeft: 8 }}>Restore latest</button>
        {bkMsg && <p className="settings-msg">{bkMsg}</p>}
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
