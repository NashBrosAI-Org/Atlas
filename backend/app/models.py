from typing import Literal, Optional
from pydantic import BaseModel, field_validator

Sentiment = Literal["champion", "neutral", "detractor"]
EngagementStatus = Literal["on_track", "at_risk", "blocked", "done"]
ThemeStatus = Literal["open", "watching", "resolved"]
MeetingType = Literal["teams", "zoom", "other"]
TranscriptSource = Literal["teams", "zoom", "manual"]
NoteType = Literal["general", "risk", "issue", "decision"]
KeyDateType = Literal["renewal", "qbr", "contract_end", "birthday", "milestone"]

Priority = Literal["critical", "high", "medium", "low"]
TaskStatus = Literal["open", "in_progress", "waiting", "done"]
TaskSource = Literal["manual", "email", "meeting"]
ClientStatus = Literal["active", "prospect", "dormant"]


class Client(BaseModel):
    sys_id: Optional[str] = None
    name: str
    short_code: Optional[str] = None
    status: ClientStatus = "active"
    email_domains: Optional[str] = None
    notes: Optional[str] = None


class Task(BaseModel):
    sys_id: Optional[str] = None
    title: str
    client: Optional[str] = None          # sys_id of a Client
    engagement: Optional[str] = None
    theme: Optional[str] = None
    priority: Priority = "medium"
    due_date: Optional[str] = None        # ISO date string
    promised_date: Optional[str] = None
    is_commitment: bool = False
    status: TaskStatus = "open"
    source: TaskSource = "manual"


class Contact(BaseModel):
    sys_id: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    client: Optional[str] = None
    role_title: Optional[str] = None
    reports_to: Optional[str] = None      # sys_id of another Contact
    personal_notes: Optional[str] = None
    sentiment: Sentiment = "neutral"


class Engagement(BaseModel):
    sys_id: Optional[str] = None
    name: str
    client: Optional[str] = None
    status: EngagementStatus = "on_track"
    start_date: Optional[str] = None
    target_date: Optional[str] = None
    description: Optional[str] = None


class Theme(BaseModel):
    sys_id: Optional[str] = None
    name: str
    client: Optional[str] = None
    status: ThemeStatus = "open"
    description: Optional[str] = None


class Meeting(BaseModel):
    sys_id: Optional[str] = None
    title: str
    client: Optional[str] = None
    engagement: Optional[str] = None
    datetime: Optional[str] = None
    type: MeetingType = "teams"
    attendees: Optional[str] = None
    summary: Optional[str] = None


class Transcript(BaseModel):
    sys_id: Optional[str] = None
    meeting: Optional[str] = None
    client: Optional[str] = None
    full_text: str
    source: TranscriptSource = "manual"
    captured_date: Optional[str] = None


class Note(BaseModel):
    sys_id: Optional[str] = None
    title: str
    body: Optional[str] = None
    note_type: NoteType = "general"
    target_table: Optional[str] = None    # e.g. "client", "engagement", "theme", "meeting"
    target_id: Optional[str] = None       # sys_id of the pinned record
    pinned: bool = False


class Tag(BaseModel):
    sys_id: Optional[str] = None
    name: str                             # unique, case-insensitive


class TagAttach(BaseModel):
    name: str                             # tag name; created on the fly if new


class KeyDate(BaseModel):
    sys_id: Optional[str] = None
    title: str
    type: KeyDateType = "milestone"
    date: Optional[str] = None            # ISO date (YYYY-MM-DD)
    recurring: bool = False               # annual (renewals, birthdays)
    reminder_lead_days: int = 7
    client: Optional[str] = None          # sys_id of a Client
    contact: Optional[str] = None         # sys_id of a Contact


class Link(BaseModel):
    sys_id: Optional[str] = None
    title: str
    url: Optional[str] = None             # external resource (SharePoint, Jira, docs…)
    client: Optional[str] = None          # sys_id of a Client

    @field_validator("url")
    @classmethod
    def _http_scheme_only(cls, v: Optional[str]) -> Optional[str]:
        """Reject non-http(s) URLs (e.g. javascript:/data:) — they would become a
        stored-XSS sink when rendered as an anchor href in the dossier."""
        if v and not v.strip().lower().startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return v
