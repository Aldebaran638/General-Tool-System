"""
backend/tests/modules/okr/test_departments.py
部门 CRUD + 重名 400 + 有成员删除 409 + reorder 排序 + 权限
"""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.modules.okr.helpers import (
    OKR_URL,
    create_department,
    random_name,
    set_user_department,
)
from tests.utils.user import create_random_user

URL = f"{OKR_URL}/departments"


def _list_ids(client: TestClient, headers: dict[str, str]) -> list[str]:
    r = client.get(URL, headers=headers)
    assert r.status_code == 200, r.text
    return [d["id"] for d in r.json()["data"]]


# ─────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────


def test_create_department(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    name = random_name("dept")
    r = client.post(
        URL,
        headers=superuser_token_headers,
        json={"name": name, "description": "desc"},
    )
    assert r.status_code == 200, r.text
    content = r.json()
    assert content["name"] == name
    assert content["description"] == "desc"
    assert "id" in content
    assert isinstance(content["sort_order"], int)


def test_list_departments_contains_created(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    dept = create_department(client, superuser_token_headers)
    r = client.get(URL, headers=superuser_token_headers)
    assert r.status_code == 200, r.text
    content = r.json()
    assert content["count"] == len(content["data"])
    ids = [d["id"] for d in content["data"]]
    assert dept["id"] in ids


def test_create_department_duplicate_name_400(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    dept = create_department(client, superuser_token_headers)
    r = client.post(
        URL, headers=superuser_token_headers, json={"name": dept["name"]}
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Department name already exists"


def test_update_department(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    dept = create_department(client, superuser_token_headers)
    new_name = random_name("dept-renamed")
    r = client.patch(
        f"{URL}/{dept['id']}",
        headers=superuser_token_headers,
        json={"name": new_name, "description": "updated"},
    )
    assert r.status_code == 200, r.text
    content = r.json()
    assert content["name"] == new_name
    assert content["description"] == "updated"


def test_update_department_duplicate_name_400(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    dept_a = create_department(client, superuser_token_headers)
    dept_b = create_department(client, superuser_token_headers)
    r = client.patch(
        f"{URL}/{dept_b['id']}",
        headers=superuser_token_headers,
        json={"name": dept_a["name"]},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Department name already exists"


def test_update_department_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.patch(
        f"{URL}/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json={"name": random_name("dept")},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Department not found"


def test_delete_department(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    dept = create_department(client, superuser_token_headers)
    r = client.delete(f"{URL}/{dept['id']}", headers=superuser_token_headers)
    assert r.status_code == 200, r.text
    assert r.json()["message"] == "Department deleted successfully"
    assert dept["id"] not in _list_ids(client, superuser_token_headers)


def test_delete_department_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.delete(f"{URL}/{uuid.uuid4()}", headers=superuser_token_headers)
    assert r.status_code == 404
    assert r.json()["detail"] == "Department not found"


# ─────────────────────────────────────────────
# 有成员时删除 → 409
# ─────────────────────────────────────────────


def test_delete_department_with_members_409(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    dept = create_department(client, superuser_token_headers)
    user = create_random_user(db)
    set_user_department(
        client,
        superuser_token_headers,
        user_id=str(user.id),
        department_id=dept["id"],
    )

    r = client.delete(f"{URL}/{dept['id']}", headers=superuser_token_headers)
    assert r.status_code == 409
    assert r.json()["detail"] == (
        "Department still has members; reassign them before deleting"
    )

    # 成员迁走之后可以删除
    set_user_department(
        client,
        superuser_token_headers,
        user_id=str(user.id),
        department_id=None,
    )
    r = client.delete(f"{URL}/{dept['id']}", headers=superuser_token_headers)
    assert r.status_code == 200, r.text


# ─────────────────────────────────────────────
# reorder
# ─────────────────────────────────────────────


def test_reorder_departments(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    d1 = create_department(client, superuser_token_headers)
    d2 = create_department(client, superuser_token_headers)
    d3 = create_department(client, superuser_token_headers)

    new_order = [d3["id"], d1["id"], d2["id"]]
    r = client.post(
        f"{URL}/reorder",
        headers=superuser_token_headers,
        json={"ids": new_order},
    )
    assert r.status_code == 200, r.text
    assert r.json()["message"] == "Departments reordered successfully"

    # 全量列表按 sort_order 排序，过滤出这三个，相对顺序必须等于新顺序
    listed = _list_ids(client, superuser_token_headers)
    mine = [i for i in listed if i in set(new_order)]
    assert mine == new_order


# ─────────────────────────────────────────────
# 权限：普通成员一律 403
# ─────────────────────────────────────────────


def test_departments_normal_user_forbidden(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    dept = create_department(client, superuser_token_headers)

    r = client.get(URL, headers=normal_user_token_headers)
    assert r.status_code == 403

    r = client.post(
        URL,
        headers=normal_user_token_headers,
        json={"name": random_name("dept")},
    )
    assert r.status_code == 403

    r = client.patch(
        f"{URL}/{dept['id']}",
        headers=normal_user_token_headers,
        json={"name": random_name("dept")},
    )
    assert r.status_code == 403

    r = client.delete(f"{URL}/{dept['id']}", headers=normal_user_token_headers)
    assert r.status_code == 403

    r = client.post(
        f"{URL}/reorder",
        headers=normal_user_token_headers,
        json={"ids": [dept["id"]]},
    )
    assert r.status_code == 403
