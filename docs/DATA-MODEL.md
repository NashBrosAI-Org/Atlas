# Atlas — Data Model

Spine entity is **Client**. Everything hangs off a Client. Table/field names mirror CSM/PPM
so a later migration is a mapping, not a rebuild (see [GUARDRAILS](GUARDRAILS.md) rule #5).

Full field-by-field definitions live in the plan's **"ServiceNow data model reference"**
section: [`superpowers/plans/2026-06-02-atlas-foundation.md`](superpowers/plans/2026-06-02-atlas-foundation.md).
This file is the at-a-glance map; the plan is authoritative for field types.

```
Client (spine)                         → future CSM Account
 ├── Engagement                        → future PPM Project   (lightweight custom table for now)
 ├── Theme                             (custom; non-Agile sense)
 ├── Contact (+ reports_to self-ref)   → future CSM Contact   (org chart + personal/relationship notes)
 └── attached items:
       Task        (priority, due_date, promised_date, is_commitment, status, source)
       Meeting     (→ has Transcript)
       Transcript  (full_text retained in SN; bulky raw kept per backup rule)
       Email       (subject/body/graph_message_id — the retained content)
       Note        (polymorphic `target` via Document ID; note_type = RAID: risk/issue/decision)
       Deck        (output_type: pptx | site)
       KeyDate     (renewal / qbr / contract_end / birthday / milestone)
       Link        (url resources per client)
       Tag / TagM2M (cross-cutting, polymorphic)
```

## Invariants
- **Client** is required context for almost every record; the cockpit slices both *across*
  clients (the "Now" view) and *into* one client (the dossier, future Plan 2/3).
- **Note.target** and **TagM2M.target** use ServiceNow's **Document ID** field type — the
  native polymorphic pointer. Don't replace it with a pile of optional reference fields.
- **RAID** is modeled as `Note.note_type` (general/risk/issue/decision), not a separate table.
- **Commitments** are `Task.is_commitment = true` + `promised_date` (what you told the client,
  distinct from the internal `due_date`). They sort ahead at equal priority/date in the Now view.

## Status / current build
- Plan 1 builds **all tables in SN** but the app only wires **Client + Task**.
- Contacts, Notes/RAID, Engagements, Themes, Meetings, Transcripts → Plan 2.
- Activity timeline (derived), Links, Tags, KeyDates, export/backup job → Plan 3.
