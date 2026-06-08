"""One-time historical backload of exported mail/calendar/transcripts into Atlas.

The user exports files on their Mac (no IT/app-registration needed):
  • email      → .eml   (drag messages from Outlook to Finder)
  • calendar   → .ics   (Calendar.app File→Export, or drag events)
  • transcripts→ .vtt   (download per Teams meeting)

This module parses those into the **Graph-shaped** dicts Atlas already understands,
then POSTs mail+events to /api/m365/ingest (reusing the tested normalize/match/dedup/
flagged→task pipeline) and transcripts to /api/transcripts. Claude is NOT in this path,
so a backload of any size costs zero tokens. Retention into ServiceNow stays risk R1 —
scope your export to client domains + a sensible window.

Parsers are pure/stdlib-only (no new deps) so they unit-test cleanly. Run the CLI:
    cd backend && python -m app.backload --email ~/atlas-export/email \\
        --calendar ~/atlas-export/calendar --transcripts ~/atlas-export/transcripts
"""
from __future__ import annotations

import email
import re
from email import policy
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------- email (.eml)

def _strip_html(html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+\n", "\n", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def _eml_body(msg: email.message.EmailMessage) -> str:
    try:
        part = msg.get_body(preferencelist=("plain", "html"))
        if part is None:
            return ""
        content = part.get_content()
        if part.get_content_type() == "text/html":
            content = _strip_html(content)
        return content.strip()
    except Exception:
        payload = msg.get_payload(decode=False)
        return payload if isinstance(payload, str) else ""


def eml_to_message(raw: bytes) -> dict:
    """Parse a .eml byte string into a Graph v1.0-shaped message dict. `id` uses the
    RFC Message-ID header so re-imports (or later live-bridging the same mail) dedup."""
    msg = email.message_from_bytes(raw, policy=policy.default)
    mid = (msg["Message-ID"] or "").strip().strip("<>")
    subject = str(msg["Subject"] or "")
    from_pairs = getaddresses([msg["From"]]) if msg["From"] else []
    from_addr = from_pairs[0][1] if from_pairs else ""
    to_addrs = [a for _, a in getaddresses(msg.get_all("To", [])) if a]
    received = ""
    if msg["Date"]:
        try:
            received = parsedate_to_datetime(msg["Date"]).isoformat()
        except (TypeError, ValueError):
            received = str(msg["Date"])
    return {
        # fall back to a stable synthetic id if Message-ID is absent
        "id": mid or f"eml::{from_addr}::{received}::{subject}",
        "subject": subject,
        "receivedDateTime": received,
        "from": {"emailAddress": {"address": from_addr}},
        "toRecipients": [{"emailAddress": {"address": a}} for a in to_addrs],
        "body": {"content": _eml_body(msg)},
        "flag": {"flagStatus": "notFlagged"},
    }


# -------------------------------------------------------------- calendar (.ics)

def _unescape_ics(value: str) -> str:
    return value.replace("\\,", ",").replace("\\;", ";").replace("\\n", "\n").replace("\\N", "\n")


def _ics_datetime(value: str) -> str:
    """Normalize an iCalendar date/date-time to an ISO-ish string.
    20260610T150000Z → 2026-06-10T15:00:00Z ; 20260610 → 2026-06-10."""
    v = value.strip()
    m = re.match(r"^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2})(Z)?)?$", v)
    if not m:
        return v
    y, mo, d, hh, mm, ss, z = m.groups()
    if hh is None:
        return f"{y}-{mo}-{d}"
    return f"{y}-{mo}-{d}T{hh}:{mm}:{ss}{'Z' if z else ''}"


def _ics_mailto(value: str) -> str:
    return value.strip().split(":")[-1].strip().lower() if "mailto" in value.lower() else ""


def parse_ics(text: str) -> list[dict]:
    """Parse an .ics document into Graph v1.0-shaped event dicts (one per VEVENT).
    `id` uses the VEVENT UID for dedup."""
    # unfold continuation lines (a leading space/tab continues the previous line)
    unfolded: list[str] = []
    for raw in text.splitlines():
        if raw[:1] in (" ", "\t") and unfolded:
            unfolded[-1] += raw[1:]
        else:
            unfolded.append(raw)

    events: list[dict] = []
    cur: Optional[dict] = None
    for line in unfolded:
        if line.startswith("BEGIN:VEVENT"):
            cur = {"uid": "", "summary": "", "dtstart": "", "attendees": [], "online": False}
        elif line.startswith("END:VEVENT"):
            if cur is not None:
                events.append({
                    "id": cur["uid"],
                    "subject": cur["summary"],
                    "start": {"dateTime": cur["dtstart"]},
                    "attendees": [{"emailAddress": {"address": a}} for a in cur["attendees"]],
                    "isOnlineMeeting": cur["online"],
                })
            cur = None
        elif cur is not None:
            name, sep, value = line.partition(":")
            if not sep:
                continue
            key = name.split(";", 1)[0].upper()
            if key == "UID":
                cur["uid"] = value.strip()
            elif key == "SUMMARY":
                cur["summary"] = _unescape_ics(value)
            elif key == "DTSTART":
                cur["dtstart"] = _ics_datetime(value)
            elif key == "ATTENDEE":
                addr = _ics_mailto(value)
                if addr:
                    cur["attendees"].append(addr)
            elif key in ("LOCATION", "X-MICROSOFT-SKYPETEAMSMEETINGURL") or "TEAMS" in key:
                if re.search(r"teams\.microsoft|skype", value, re.I):
                    cur["online"] = True
    return events


# ------------------------------------------------------------ transcript (.vtt)

def vtt_to_text(text: str) -> str:
    """Flatten a WebVTT transcript to plain text, keeping speaker labels and dropping
    cue numbers, timing lines, and inline tags."""
    out: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s == "WEBVTT" or s.startswith(("NOTE", "STYLE", "REGION")):
            continue
        if "-->" in s or re.fullmatch(r"\d+", s):
            continue
        s = re.sub(r"<v\s+([^>]+)>", r"\1: ", s)   # <v Jane>… → "Jane: …"
        s = re.sub(r"</?[^>]+>", "", s)              # drop remaining tags/timestamps
        s = s.strip()
        if s:
            out.append(s)
    return "\n".join(out).strip()


# --------------------------------------------------------------------- CLI

def _read_dir(path: Optional[str], suffix: str) -> list[Path]:
    if not path:
        return []
    p = Path(path).expanduser()
    if p.is_file():
        return [p] if p.suffix.lower() == suffix else []
    return sorted(f for f in p.rglob(f"*{suffix}") if f.is_file())


def _post(client, url: str, json: dict) -> dict:
    r = client.post(url, json=json, timeout=120)
    r.raise_for_status()
    return r.json()


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    import httpx

    ap = argparse.ArgumentParser(description="Backload exported M365 data into Atlas.")
    ap.add_argument("--email", help="dir of .eml files")
    ap.add_argument("--calendar", help=".ics file or dir of .ics files")
    ap.add_argument("--transcripts", help="dir of .vtt files")
    ap.add_argument("--api", default="http://localhost:8000", help="Atlas backend URL")
    ap.add_argument("--client", help="sys_id to attach imported transcripts to (optional)")
    ap.add_argument("--batch", type=int, default=200, help="messages/events per ingest POST")
    ap.add_argument("--dry-run", action="store_true", help="parse + report counts, no POST")
    args = ap.parse_args(argv)

    messages = [eml_to_message(f.read_bytes()) for f in _read_dir(args.email, ".eml")]
    events: list[dict] = []
    for f in _read_dir(args.calendar, ".ics"):
        events.extend(parse_ics(f.read_text(errors="replace")))
    transcripts = [vtt_to_text(f.read_text(errors="replace")) for f in _read_dir(args.transcripts, ".vtt")]
    transcripts = [t for t in transcripts if t]

    print(f"parsed: {len(messages)} email · {len(events)} events · {len(transcripts)} transcripts")
    if args.dry_run:
        return 0

    with httpx.Client() as client:
        totals = {"ingested": 0, "skipped": 0, "tasks_created": 0, "meetings": 0}
        for i in range(0, max(len(messages), 1), args.batch) if messages else []:
            res = _post(client, f"{args.api}/api/m365/ingest", {"messages": messages[i:i + args.batch]})
            mail = res.get("mail", {})
            for k in ("ingested", "skipped", "tasks_created"):
                totals[k] += mail.get(k, 0)
        for i in range(0, len(events), args.batch):
            res = _post(client, f"{args.api}/api/m365/ingest", {"events": events[i:i + args.batch]})
            totals["meetings"] += res.get("calendar", {}).get("ingested", 0)
        for text in transcripts:
            body = {"full_text": text, "source": "teams"}
            if args.client:
                body["client"] = args.client
            _post(client, f"{args.api}/api/transcripts", body)

    print(f"imported: {totals['ingested']} email ({totals['skipped']} dup), "
          f"{totals['meetings']} meetings, {totals['tasks_created']} flagged→tasks, "
          f"{len(transcripts)} transcripts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
