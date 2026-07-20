"""
backend/tests/modules/okr/test_stats.py
聚合视图：GET /okr/stats/by-department、GET /okr/stats/by-user
"""

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.modules.okr.helpers import (
    OKR_URL,
    create_department,
    create_kr,
    create_objective,
    new_user_headers,
    set_user_department,
)

TODAY = date.today()
START = TODAY - timedelta(days=10)
DEADLINE = TODAY + timedelta(days=30)


def _setup(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> dict:
    """一个部门、两个成员、两个 objective、三条 KR（60/80/100）"""
    dept = create_department(client, superuser_token_headers)
    _, user1_id = new_user_headers(client, db)
    _, user2_id = new_user_headers(client, db)
    for uid in (user1_id, user2_id):
        set_user_department(
            client, superuser_token_headers, user_id=uid, department_id=dept["id"]
        )
    obj1 = create_objective(client, superuser_token_headers)
    obj2 = create_objective(client, superuser_token_headers)
    kr1 = create_kr(
        client, superuser_token_headers,
        objective_id=obj1["id"], assignee_id=user1_id,
        start_date=START, deadline=DEADLINE, progress=60,
    )
    kr2 = create_kr(
        client, superuser_token_headers,
        objective_id=obj2["id"], assignee_id=user1_id,
        start_date=START, deadline=DEADLINE, progress=80,
    )
    kr3 = create_kr(
        client, superuser_token_headers,
        objective_id=obj1["id"], assignee_id=user2_id,
        start_date=START, deadline=DEADLINE, progress=100,
    )
    return {
        "dept": dept, "user1_id": user1_id, "user2_id": user2_id,
        "obj1": obj1, "obj2": obj2, "kr1": kr1, "kr2": kr2, "kr3": kr3,
    }


def test_stats_by_department(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    ctx = _setup(client, superuser_token_headers, db)
    r = client.get(f"{OKR_URL}/stats/by-department", headers=superuser_token_headers)
    assert r.status_code == 200, r.text
    entries = [e for e in r.json()["data"] if e["department"]["id"] == ctx["dept"]["id"]]
    assert len(entries) == 1
    entry = entries[0]

    assert entry["department"]["name"] == ctx["dept"]["name"]
    assert entry["member_count"] == 2
    assert entry["kr_count"] == 3
    assert entry["avg_progress"] == 80  # round((60+80+100)/3)
    assert entry["objective_count"] == 2

    # 按 objective 分组
    groups = {g["objective_id"]: g for g in entry["objectives"]}
    assert set(groups) == {ctx["obj1"]["id"], ctx["obj2"]["id"]}
    g1 = groups[ctx["obj1"]["id"]]
    assert g1["objective_title"] == ctx["obj1"]["title"]
    assert {k["id"] for k in g1["krs"]} == {ctx["kr1"]["id"], ctx["kr3"]["id"]}
    g2 = groups[ctx["obj2"]["id"]]
    assert g2["objective_title"] == ctx["obj2"]["title"]
    assert [k["id"] for k in g2["krs"]] == [ctx["kr2"]["id"]]


def test_stats_by_department_empty_department(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    dept = create_department(client, superuser_token_headers)
    r = client.get(f"{OKR_URL}/stats/by-department", headers=superuser_token_headers)
    assert r.status_code == 200, r.text
    entries = [e for e in r.json()["data"] if e["department"]["id"] == dept["id"]]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["member_count"] == 0
    assert entry["kr_count"] == 0
    assert entry["avg_progress"] == 0
    assert entry["objective_count"] == 0
    assert entry["objectives"] == []


def test_stats_by_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    ctx = _setup(client, superuser_token_headers, db)
    r = client.get(f"{OKR_URL}/stats/by-user", headers=superuser_token_headers)
    assert r.status_code == 200, r.text
    by_id = {e["user"]["id"]: e for e in r.json()["data"]}

    u1 = by_id[ctx["user1_id"]]
    assert u1["kr_count"] == 2
    assert u1["avg_progress"] == 70  # round((60+80)/2)
    assert {k["id"] for k in u1["krs"]} == {ctx["kr1"]["id"], ctx["kr2"]["id"]}
    assert u1["department"] == {"id": ctx["dept"]["id"], "name": ctx["dept"]["name"]}

    u2 = by_id[ctx["user2_id"]]
    assert u2["kr_count"] == 1
    assert u2["avg_progress"] == 100
    assert [k["id"] for k in u2["krs"]] == [ctx["kr3"]["id"]]


def test_stats_by_user_no_krs(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _, user_id = new_user_headers(client, db)
    r = client.get(f"{OKR_URL}/stats/by-user", headers=superuser_token_headers)
    assert r.status_code == 200, r.text
    by_id = {e["user"]["id"]: e for e in r.json()["data"]}
    entry = by_id[user_id]
    assert entry["kr_count"] == 0
    assert entry["avg_progress"] == 0
    assert entry["krs"] == []
    assert entry["department"] is None


def test_stats_normal_user_forbidden(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{OKR_URL}/stats/by-department", headers=normal_user_token_headers
    )
    assert r.status_code == 403
    r = client.get(f"{OKR_URL}/stats/by-user", headers=normal_user_token_headers)
    assert r.status_code == 403
