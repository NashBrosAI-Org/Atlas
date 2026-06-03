# Sharing Atlas

Atlas is a local macOS app: a FastAPI backend + React UI packaged into `Atlas.app`,
talking to *your own* ServiceNow instance. There is no server to host. Sharing it
means giving someone the source and having them build it locally (which is also why
no Apple Developer ID is needed — a locally built app isn't quarantined by Gatekeeper).

## What a recipient needs

- **macOS** with **Node.js** and a **Python 3.10–3.13** (PyInstaller doesn't support 3.14).
  `brew install node python@3.12` covers both.
- A copy of this repository (git clone if they have access, or a zip of the source).
- Their own **ServiceNow instance** with the **Atlas scoped app installed** (see the in-app
  Help screen) — only required to use real data; demo mode needs nothing.

## Install (one command)

From the repository folder:

```bash
bash scripts/install.sh
```

This builds `Atlas.app` on their machine and installs it to `~/Applications`, then opens it.
Because it's built locally, macOS launches it with no "unidentified developer" prompt.
Re-run the same command to update.

## First run

Atlas opens on demo data. To connect a real instance, follow the in-app **Help** screen:
install the Atlas scoped app on the instance, then enter the instance URL + a (non-MFA)
username + password in **Settings** and **Test connection**. The password is stored in the
macOS Keychain.

## Heads-up (compliance)

Routing another organisation's email/meeting/ServiceNow content through Atlas broadens the
data-handling surface. Each user owns that with their own IT (see risk R5 in CLAUDE.md).
