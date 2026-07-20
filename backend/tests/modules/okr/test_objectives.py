"""
backend/tests/modules/okr/test_objectives.py
Objective：创建默认计算字段、有 KR 删除 409、删 KR 后可删、权限
"""

import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.modules.okr.helpers import (
    OKR_URL,
    create_kr,
    create_objective,
    get_objective,
    new_user_headers,
    random_name,
)

URL = f"{OKR_URL}/objectives"
TODAY = date.today()


def test_create_objective_defaults(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.post(
        URL,
        headers=superuser_token_headers,
        json={"title": random_name("obj"), "description": "desc"},
    )
    assert r.status_code == 200, r.text
    content = r.json()
    assert content["progress"] == 0
    assert content["kr_count"] == 0
    assert content["time_range"] is None
    assert "id" in content
    assert "created_by_id" in content


def test_list_objectives_contains_created(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    obj = create_objective(client, superuser_token_headers)
    r = client.get(URL, headers=superuser_token_headers)
    assert r.status_code == 200, r.text
    content = r.json()
    assert content["count"] == len(content["data"])
    found = get_objective(client, superuser_token_headers, obj["id"])
    assert found["title"] == obj["title"]
    assert found["progress"] == 0
    assert found["kr_count"] == 0
    assert found["time_range"] is None


def test_update_objective(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    obj = create_objective(client, superuser_token_headers)
    new_title = random_name("obj-renamed")
    r = client.patch(
        f"{URL}/{obj['id']}",
        headers=superuser_token_headers,
        json={"title": new_title, "description": "updated"},
    )
    assert r.status_code == 200, r.text
    content = r.json()
    assert content["title"] == new_title
    assert content["description"] == "updated"


def test_update_objective_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.patch(
        f"{URL}/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json={"title": random_name("obj")},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Objective not found"


def test_delete_objective(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    obj = create_objective(client, superuser_token_headers)
    r = client.delete(f"{URL}/{obj['id']}", headers=superuser_token_headers)
    assert r.status_code == 200, r.text
    assert r.json()["message"] == "Objective deleted successfully"

    r = client.get(URL, headers=superuser_token_headers)
    ids = [o["id"] for o in r.json()["data"]]
    assert obj["id"] not in ids


def test_delete_objective_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.delete(f"{URL}/{uuid.uuid4()}", headers=superuser_token_headers)
    assert r.status_code == 404
    assert r.json()["detail"] == "Objective not found"


def test_delete_objective_with_krs_409_then_deletable(
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
    )

    # 有 KR 时删除 → 409
    r = client.delete(f"{URL}/{obj['id']}", headers=superuser_token_headers)
    assert r.status_code == 409
    assert r.json()["detail"] == "Objective still has key results; delete them first"

    # 删掉 KR 之后可删
    r = client.delete(f"{OKR_URL}/krs/{kr['id']}", headers=superuser_token_headers)
    assert r.status_code == 200, r.text
    r = client.delete(f"{URL}/{obj['id']}", headers=superuser_token_headers)
    assert r.status_code == 200, r.text


def test_objectives_normal_user_forbidden(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    obj = create_objective(client, superuser_token_headers)

    r = client.get(URL, headers=normal_user_token_headers)
    assert r.status_code == 403

    r = client.post(
        URL, headers=normal_user_token_headers, json={"title": random_name("obj")}
    )
    assert r.status_code == 403

    r = client.patch(
        f"{URL}/{obj['id']}",
        headers=normal_user_token_headers,
        json={"title": random_name("obj")},
    )
    assert r.status_code == 403

    r = client.delete(f"{URL}/{obj['id']}", headers=normal_user_token_headers)
    assert r.status_code == 403
