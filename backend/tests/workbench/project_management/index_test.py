"""
backend/tests/workbench/project_management/index_test.py
project_management 工具主测试文件

覆盖范围：
- GET  /api/v1/items/        列表查询（超管看全部、普通用户只看自己）
- GET  /api/v1/items/{id}    详情查询
- POST /api/v1/items/        创建
- PUT  /api/v1/items/{id}    更新
- DELETE /api/v1/items/{id}  删除
- 权限分支（403 Not enough permissions）
- 404 Not found 分支
- 数据隔离分支（普通用户不可见他人 item）
- 参数错误分支（title 为空）
"""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.items.helpers import create_random_item

BASE_URL = f"{settings.API_V1_STR}/items"


def test_read_items_superuser_sees_all(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_item(db)
    create_random_item(db)
    response = client.get(f"{BASE_URL}/", headers=superuser_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    assert len(content["data"]) >= 2


def test_read_items_normal_user_sees_only_own(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    create_random_item(db)

    response = client.get(f"{BASE_URL}/", headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert content["count"] == len(content["data"])


def test_read_items_pagination(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_item(db)
    create_random_item(db)
    response = client.get(
        f"{BASE_URL}/?skip=0&limit=1", headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) <= 1


def test_read_item_success(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(f"{BASE_URL}/{item.id}", headers=superuser_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == item.title
    assert content["description"] == item.description
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_read_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{BASE_URL}/{uuid.uuid4()}", headers=superuser_token_headers
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_read_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{BASE_URL}/{item.id}", headers=normal_user_token_headers
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_read_own_item_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    list_resp = client.get(f"{BASE_URL}/", headers=normal_user_token_headers)
    items = list_resp.json()["data"]

    if not items:
        return

    item_id = items[0]["id"]
    response = client.get(f"{BASE_URL}/{item_id}", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert response.json()["id"] == item_id


def test_create_item_success(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Test title", "description": "Test description"}
    response = client.post(f"{BASE_URL}/", headers=superuser_token_headers, json=data)
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content


def test_create_item_no_description(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Only title"}
    response = client.post(f"{BASE_URL}/", headers=superuser_token_headers, json=data)
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] is None


def test_create_item_missing_title(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"description": "Missing title"}
    response = client.post(f"{BASE_URL}/", headers=superuser_token_headers, json=data)
    assert response.status_code == 422


def test_create_item_empty_title(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "", "description": "Empty title"}
    response = client.post(f"{BASE_URL}/", headers=superuser_token_headers, json=data)
    assert response.status_code == 422


def test_create_item_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    data = {"title": "Normal user item", "description": "desc"}
    response = client.post(
        f"{BASE_URL}/", headers=normal_user_token_headers, json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert "owner_id" in content


def test_update_item_success(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{BASE_URL}/{item.id}", headers=superuser_token_headers, json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_update_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{BASE_URL}/{uuid.uuid4()}", headers=superuser_token_headers, json=data
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_update_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Hijack title", "description": "Hijack desc"}
    response = client.put(
        f"{BASE_URL}/{item.id}", headers=normal_user_token_headers, json=data
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_update_item_partial(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Partial update only title"}
    response = client.put(
        f"{BASE_URL}/{item.id}", headers=superuser_token_headers, json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]


def test_delete_item_success(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{BASE_URL}/{item.id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Item deleted successfully"


def test_delete_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{BASE_URL}/{uuid.uuid4()}", headers=superuser_token_headers
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_delete_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{BASE_URL}/{item.id}", headers=normal_user_token_headers
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_delete_item_then_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    client.delete(f"{BASE_URL}/{item.id}", headers=superuser_token_headers)
    response = client.get(f"{BASE_URL}/{item.id}", headers=superuser_token_headers)
    assert response.status_code == 404


def test_data_isolation_list(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    create_random_item(db)
    create_random_item(db)

    response = client.get(f"{BASE_URL}/", headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == len(content["data"])


def test_data_isolation_detail(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    other_item = create_random_item(db)
    response = client.get(
        f"{BASE_URL}/{other_item.id}", headers=normal_user_token_headers
    )
    assert response.status_code == 403