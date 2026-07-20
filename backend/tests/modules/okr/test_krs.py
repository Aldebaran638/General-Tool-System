"""
backend/tests/modules/okr/test_krs.py
KR：CRUD、objective 计算字段（progress 均值 / kr_count / time_range）、
进度更新权限矩阵、department 由 assignee 派生
"""

import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.modules.okr.helpers import (
    OKR_URL,
    create_department,
    create_kr,
    create_objective,
    get_objective,
    new_user_headers,
    random_name,
    set_user_department,
)
from tests.utils.user import create_random_user

URL = f"{OKR_URL}/krs"
TODAY = date.today()


# ─────────────────────────────────────────────
# 创建 + objective 计算字段
# ─────────────────────────────────────────────


def test_create_kr(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    obj = create_objective(client, superuser_token_headers)
    _, user_id = new_user_headers(client, db)
    start = TODAY - timedelta(days=5)
    deadline = TODAY + timedelta(days=20)
    r = client.post(
        URL,
        headers=superuser_token_headers,
        json={
            "objective_id": obj["id"],
            "assignee_id": user_id,
            "title": random_name("kr"),
            "start_date": start.isoformat(),
            "deadline": deadline.isoformat(),
            "progress": 30,
        },
    )
    assert r.status_code == 200, r.text
    content = r.json()
    assert content["objective_id"] == obj["id"]
    assert content["progress"] == 30
    assert content["start_date"] == start.isoformat()
    assert content["deadline"] == deadline.isoformat()
    assert content["assignee"]["id"] == user_id


def test_objective_stats_progress_and_time_range(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """两个 KR 70/70 → objective progress=70、kr_count=2、time_range=min(start)/max(deadline)"""
    obj = create_objective(client, superuser_token_headers)
    _, user_id = new_user_headers(client, db)
    start_min = TODAY - timedelta(days=10)
    start_other = TODAY - timedelta(days=3)
    deadline_other = TODAY + timedelta(days=5)
    deadline_max = TODAY + timedelta(days=30)
    create_kr(
        client,
        superuser_token_headers,
        objective_id=obj["id"],
        assignee_id=user_id,
        start_date=start_min,
        deadline=deadline_other,
        progress=70,
    )
    create_kr(
        client,
        superuser_token_headers,
        objective_id=obj["id"],
        assignee_id=user_id,
        start_date=start_other,
        deadline=deadline_max,
        progress=70,
    )

    found = get_objective(client, superuser_token_headers, obj["id"])
    assert found["kr_count"] == 2
    assert found["progress"] == 70
    assert found["time_range"] == {
        "start": start_min.isoformat(),
        "end": deadline_max.isoformat(),
    }


def test_objective_progress_average_100_and_0(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """100/0 → 均值 50"""
    obj = create_objective(client, superuser_token_headers)
    _, user_id = new_user_headers(client, db)
    for progress in (100, 0):
        create_kr(
            client,
            superuser_token_headers,
            objective_id=obj["id"],
            assignee_id=user_id,
            start_date=TODAY,
            deadline=TODAY + timedelta(days=7),
            progress=progress,
        )

    found = get_objective(client, superuser_token_headers, obj["id"])
    assert found["kr_count"] == 2
    assert found["progress"] == 50


def test_create_kr_objective_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _, user_id = new_user_headers(client, db)
    r = client.post(
        URL,
        headers=superuser_token_headers,
        json={
            "objective_id": str(uuid.uuid4()),
            "assignee_id": user_id,
            "title": random_name("kr"),
            "start_date": TODAY.isoformat(),
            "deadline": (TODAY + timedelta(days=7)).isoformat(),
        },
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Objective not found"


def test_create_kr_assignee_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    obj = create_objective(client, superuser_token_headers)
    r = client.post(
        URL,
        headers=superuser_token_headers,
        json={
            "objective_id": obj["id"],
            "assignee_id": str(uuid.uuid4()),
            "title": random_name("kr"),
            "start_date": TODAY.isoformat(),
            "deadline": (TODAY + timedelta(days=7)).isoformat(),
        },
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Assignee not found"


# ─────────────────────────────────────────────
# 读 / 改 / 删
# ─────────────────────────────────────────────


def test_read_objective_krs(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    obj = create_objective(client, superuser_token_headers)
    _, user_id = new_user_headers(client, db)
    kr = create_kr(
        client,
        superuser_token_headers,
        objective_id=obj["id"],
        assignee_id=user_id,
        start_date=TODAY,
        deadline=TODAY + timedelta(days=7),
        progress=40,
    )
    r = client.get(
        f"{OKR_URL}/objectives/{obj['id']}/krs", headers=superuser_token_headers
    )
    assert r.status_code == 200, r.text
    content = r.json()
    assert content["count"] == 1
    assert content["data"][0]["id"] == kr["id"]
    assert content["data"][0]["assignee"]["id"] == user_id


def test_read_objective_krs_objective_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{OKR_URL}/objectives/{uuid.uuid4()}/krs", headers=superuser_token_headers
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Objective not found"


def test_update_kr(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    obj = create_objective(client, superuser_token_headers)
    _, user_id = new_user_headers(client, db)
    kr = create_kr(
        client,
        superuser_token_headers,
        objective_id=obj["id"],
        assignee_id=user_id,
        start_date=TODAY,
        deadline=TODAY + timedelta(days=7),
        progress=10,
    )
    new_title = random_name("kr-renamed")
    r = client.patch(
        f"{URL}/{kr['id']}",
        headers=superuser_token_headers,
        json={"title": new_title, "progress": 55},
    )
    assert r.status_code == 200, r.text
    content = r.json()
    assert content["title"] == new_title
    assert content["progress"] == 55


def test_update_kr_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.patch(
        f"{URL}/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json={"title": random_name("kr")},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Key result not found"


def test_delete_kr(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    obj = create_objective(client, superuser_token_headers)
    _, user_id = new_user_headers(client, db)
    kr = create_kr(
        client,
        superuser_token_headers,
        objective_id=obj["id"],
        assignee_id=user_id,
        start_date=TODAY,
        deadline=TODAY + timedelta(days=7),
        progress=10,
    )
    r = client.delete(f"{URL}/{kr['id']}", headers=superuser_token_headers)
    assert r.status_code == 200, r.text
    assert r.json()["message"] == "Key result deleted successfully"

    found = get_objective(client, superuser_token_headers, obj["id"])
    assert found["kr_count"] == 0
    assert found["progress"] == 0
    assert found["time_range"] is None


def test_delete_kr_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.delete(f"{URL}/{uuid.uuid4()}", headers=superuser_token_headers)
    assert r.status_code == 404
    assert r.json()["detail"] == "Key result not found"


# ─────────────────────────────────────────────
# department 由 assignee 派生（不存储）
# ─────────────────────────────────────────────


def test_kr_department_derived_from_assignee(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    dept_a = create_department(client, superuser_token_headers)
    dept_b = create_department(client, superuser_token_headers)
    _, user_id = new_user_headers(client, db)
    set_user_department(
        client, superuser_token_headers, user_id=user_id, department_id=dept_a["id"]
    )
    obj = create_objective(client, superuser_token_headers)
    kr = create_kr(
        client,
        superuser_token_headers,
        objective_id=obj["id"],
        assignee_id=user_id,
        start_date=TODAY,
        deadline=TODAY + timedelta(days=7),
    )

    r = client.get(
        f"{OKR_URL}/objectives/{obj['id']}/krs", headers=superuser_token_headers
    )
    mine = [k for k in r.json()["data"] if k["id"] == kr["id"]]
    assert len(mine) == 1
    assert mine[0]["department"] == {"id": dept_a["id"], "name": dept_a["name"]}

    # 改了用户的 department_id，同一 KR 的 department 跟着变
    set_user_department(
        client, superuser_token_headers, user_id=user_id, department_id=dept_b["id"]
    )
    r = client.get(
        f"{OKR_URL}/objectives/{obj['id']}/krs", headers=superuser_token_headers
    )
    mine = [k for k in r.json()["data"] if k["id"] == kr["id"]]
    assert len(mine) == 1
    assert mine[0]["department"] == {"id": dept_b["id"], "name": dept_b["name"]}


def test_kr_department_none_when_assignee_has_no_department(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    obj = create_objective(client, superuser_token_headers)
    _, user_id = new_user_headers(client, db)  # 新用户无部门
    kr = create_kr(
        client,
        superuser_token_headers,
        objective_id=obj["id"],
        assignee_id=user_id,
        start_date=TODAY,
        deadline=TODAY + timedelta(days=7),
    )
    r = client.get(
        f"{OKR_URL}/objectives/{obj['id']}/krs", headers=superuser_token_headers
    )
    mine = [k for k in r.json()["data"] if k["id"] == kr["id"]]
    assert len(mine) == 1
    assert mine[0]["department"] is None


# ─────────────────────────────────────────────
# 进度更新权限矩阵
# ─────────────────────────────────────────────


def test_update_progress_own_kr_as_member(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    headers, user_id = new_user_headers(client, db)
    obj = create_objective(client, superuser_token_headers)
    kr = create_kr(
        client,
        superuser_token_headers,
        objective_id=obj["id"],
        assignee_id=user_id,
        start_date=TODAY,
        deadline=TODAY + timedelta(days=7),
        progress=10,
    )
    r = client.patch(
        f"{URL}/{kr['id']}/progress", headers=headers, json={"progress": 80}
    )
    assert r.status_code == 200, r.text
    assert r.json()["progress"] == 80


def test_update_progress_others_kr_forbidden(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    owner_headers, owner_id = new_user_headers(client, db)
    other_headers, _ = new_user_headers(client, db)
    obj = create_objective(client, superuser_token_headers)
    kr = create_kr(
        client,
        superuser_token_headers,
        objective_id=obj["id"],
        assignee_id=owner_id,
        start_date=TODAY,
        deadline=TODAY + timedelta(days=7),
        progress=10,
    )
    r = client.patch(
        f"{URL}/{kr['id']}/progress", headers=other_headers, json={"progress": 80}
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "You can only update your own key results"

    # 负责人的数据没被改动
    r = client.get(f"{URL}/my", headers=owner_headers)
    mine = [k for k in r.json()["data"] if k["id"] == kr["id"]]
    assert len(mine) == 1
    assert mine[0]["progress"] == 10


def test_update_progress_any_kr_as_superuser(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _, user_id = new_user_headers(client, db)
    obj = create_objective(client, superuser_token_headers)
    kr = create_kr(
        client,
        superuser_token_headers,
        objective_id=obj["id"],
        assignee_id=user_id,
        start_date=TODAY,
        deadline=TODAY + timedelta(days=7),
        progress=10,
    )
    r = client.patch(
        f"{URL}/{kr['id']}/progress",
        headers=superuser_token_headers,
        json={"progress": 100},
    )
    assert r.status_code == 200, r.text
    assert r.json()["progress"] == 100


def test_update_progress_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.patch(
        f"{URL}/{uuid.uuid4()}/progress",
        headers=superuser_token_headers,
        json={"progress": 50},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Key result not found"


def test_update_progress_out_of_range_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    headers, user_id = new_user_headers(client, db)
    obj = create_objective(client, superuser_token_headers)
    kr = create_kr(
        client,
        superuser_token_headers,
        objective_id=obj["id"],
        assignee_id=user_id,
        start_date=TODAY,
        deadline=TODAY + timedelta(days=7),
    )
    r = client.patch(
        f"{URL}/{kr['id']}/progress", headers=headers, json={"progress": 101}
    )
    assert r.status_code == 422
    r = client.patch(
        f"{URL}/{kr['id']}/progress", headers=headers, json={"progress": -1}
    )
    assert r.status_code == 422


# ─────────────────────────────────────────────
# 权限：普通成员对超管端点一律 403
# ─────────────────────────────────────────────


def test_krs_normal_user_forbidden(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    obj = create_objective(client, superuser_token_headers)
    other = create_random_user(db)
    kr = create_kr(
        client,
        superuser_token_headers,
        objective_id=obj["id"],
        assignee_id=str(other.id),
        start_date=TODAY,
        deadline=TODAY + timedelta(days=7),
    )

    r = client.get(
        f"{OKR_URL}/objectives/{obj['id']}/krs", headers=normal_user_token_headers
    )
    assert r.status_code == 403

    r = client.post(
        URL,
        headers=normal_user_token_headers,
        json={
            "objective_id": obj["id"],
            "assignee_id": str(other.id),
            "title": random_name("kr"),
            "start_date": TODAY.isoformat(),
            "deadline": (TODAY + timedelta(days=7)).isoformat(),
        },
    )
    assert r.status_code == 403

    r = client.patch(
        f"{URL}/{kr['id']}",
        headers=normal_user_token_headers,
        json={"title": random_name("kr")},
    )
    assert r.status_code == 403

    r = client.delete(f"{URL}/{kr['id']}", headers=normal_user_token_headers)
    assert r.status_code == 403
