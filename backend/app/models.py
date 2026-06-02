from typing import Literal, Optional
from pydantic import BaseModel

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
