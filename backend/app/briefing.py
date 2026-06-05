"""Morning briefing: a single read-model that aggregates the day — the
deterministic Now tasks, today's meetings, due key-date reminders, and the
stale-client radar. Pure aggregation over existing records (no new storage, no
Graph), mirroring app/awareness.py."""
from datetime import date, datetime, time, timezone
from typing import Optional

from app import awareness, reminders
from app.ordering import active_now_tasks
from app.servicenow import ServiceNowClient


async def build_briefing(sn: ServiceNowClient, scope: str, today: Optional[date] = None,
                         now_limit: int = 5, cooling_days: int = 14,
                         stale_days: int = 30) -> dict:
    today = today or date.today()

    now_tasks = active_now_tasks(await sn.list(f"{scope}_task"), now_limit)

    meetings = [m for m in await sn.list(f"{scope}_meeting")
                if (m.get("datetime") or "")[:10] == today.isoformat()]

    due = await reminders.due_reminders(sn, scope, today)
    radar_now = datetime.combine(today, time(0, 0), tzinfo=timezone.utc)
    radar = await awareness.stale_radar(sn, scope, cooling_days, stale_days, now=radar_now)

    return {
        "date": today.isoformat(),
        "now_tasks": now_tasks,
        "todays_meetings": meetings,
        "reminders": due,
        "radar": radar,
    }
