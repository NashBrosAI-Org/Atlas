from app.models import Task, Client

def test_task_defaults():
    t = Task(title="Send SOW", client="abc123")
    assert t.priority == "medium"
    assert t.status == "open"
    assert t.is_commitment is False
    assert t.source == "manual"

def test_client_minimal():
    c = Client(name="Acme Corp")
    assert c.status == "active"
    assert c.sys_id is None
