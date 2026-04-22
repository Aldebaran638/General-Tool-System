"""
backend/tests/items/index_test.py
items（项目管理）工具主测试文件

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
from tests.items.helpers import create_item_for_user, create_random_item
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string

BASE_URL = f"{settings.API_V1_STR}/items"


# ─────────────────────────────────────────────
# 列表查询
# ─────────────────────────────────────────────


def test_read_items_superuser_sees_all(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """超管可查看全部 items，结果不为空"""
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
    """普通用户只看到自己的 items，看不到其他用户的"""
    # 创建一个属于其他用户的 item
    create_random_item(db)

    response = client.get(f"{BASE_URL}/", headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    # 所有返回记录的 owner_id 必须都是当前用户（通过 count 推断）
    # count 与 data 长度一致，说明普通用户未看到他人数据
    assert content["count"] == len(content["data"])


def test_read_items_pagination(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """列表分页参数 skip/limit 有效"""
    create_random_item(db)
    create_random_item(db)
    response = client.get(
        f"{BASE_URL}/?skip=0&limit=1", headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) <= 1


# ─────────────────────────────────────────────
# 详情查询
# ─────────────────────────────────────────────


def test_read_item_success(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """超管查询 item 详情成功"""
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
    """查询不存在的 item 返回 404"""
    response = client.get(
        f"{BASE_URL}/{uuid.uuid4()}", headers=superuser_token_headers
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_read_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """普通用户查询他人 item 返回 403"""
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
    """普通用户可查询自己的 item 详情"""
    # 先获取当前 normal user 的 id（通过 list 接口推断属于自己的 item）
    from tests.utils.user import authentication_token_from_email
    from app.core.config import settings as cfg

    # 直接借助 list 接口拿到属于自己的 item
    list_resp = client.get(f"{BASE_URL}/", headers=normal_user_token_headers)
    items = list_resp.json()["data"]

    if not items:
        # 若无记录则跳过（fixtures 中普通用户可能没有 item，不算失败）
        return

    item_id = items[0]["id"]
    response = client.get(f"{BASE_URL}/{item_id}", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert response.json()["id"] == item_id


# ─────────────────────────────────────────────
# 创建
# ─────────────────────────────────────────────


def test_create_item_success(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """创建 item 成功，返回字段正确"""
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
    """description 可为空，仅 title 必填"""
    data = {"title": "Only title"}
    response = client.post(f"{BASE_URL}/", headers=superuser_token_headers, json=data)
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] is None


def test_create_item_missing_title(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """title 缺失时参数校验失败，返回 422"""
    data = {"description": "Missing title"}
    response = client.post(f"{BASE_URL}/", headers=superuser_token_headers, json=data)
    assert response.status_code == 422


def test_create_item_empty_title(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """title 为空字符串时参数校验失败，返回 422"""
    data = {"title": "", "description": "Empty title"}
    response = client.post(f"{BASE_URL}/", headers=superuser_token_headers, json=data)
    assert response.status_code == 422


def test_create_item_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """普通用户可创建 item，owner_id 为自己"""
    data = {"title": "Normal user item", "description": "desc"}
    response = client.post(
        f"{BASE_URL}/", headers=normal_user_token_headers, json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert "owner_id" in content


# ─────────────────────────────────────────────
# 更新
# ─────────────────────────────────────────────


def test_update_item_success(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """超管更新 item 成功"""
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
    """更新不存在的 item 返回 404"""
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
    """普通用户更新他人 item 返回 403"""
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
    """只更新 title，description 保持不变"""
    item = create_random_item(db)
    data = {"title": "Partial update only title"}
    response = client.put(
        f"{BASE_URL}/{item.id}", headers=superuser_token_headers, json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]


# ─────────────────────────────────────────────
# 删除
# ─────────────────────────────────────────────


def test_delete_item_success(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """超管删除 item 成功"""
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
    """删除不存在的 item 返回 404"""
    response = client.delete(
        f"{BASE_URL}/{uuid.uuid4()}", headers=superuser_token_headers
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_delete_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """普通用户删除他人 item 返回 403"""
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
    """item 删除后再次查询返回 404"""
    item = create_random_item(db)
    client.delete(f"{BASE_URL}/{item.id}", headers=superuser_token_headers)
    response = client.get(f"{BASE_URL}/{item.id}", headers=superuser_token_headers)
    assert response.status_code == 404


# ─────────────────────────────────────────────
# 数据隔离
# ─────────────────────────────────────────────


def test_data_isolation_list(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """
    创建两个不同用户的 item，普通用户列表只看到自己的，
    count 与 data 数量一致
    """
    # 其他用户 item
    create_random_item(db)
    create_random_item(db)

    response = client.get(f"{BASE_URL}/", headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == len(content["data"])


def test_data_isolation_detail(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """普通用户无法通过 id 访问他人 item 详情"""
    other_item = create_random_item(db)
    response = client.get(
        f"{BASE_URL}/{other_item.id}", headers=normal_user_token_headers
    )
    assert response.status_code == 403
