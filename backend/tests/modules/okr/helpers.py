"""
backend/tests/modules/okr/helpers.py
OKR 模块测试辅助函数

约定：
- 所有数据都带随机后缀，测试会话内共享一个 app_test 库，互不干扰
- new_user_headers 每次创建全新普通用户，保证 /krs/my 等按人隔离的断言干净
"""

from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email, random_lower_string

OKR_URL = f"{settings.API_V1_STR}/okr"
USERS_URL = f"{settings.API_V1_STR}/users"


def random_name(prefix: str) -> str:
    return f"{prefix}-{random_lower_string()[:12]}"


def new_user_headers(client: TestClient, db: Session) -> tuple[dict[str, str], str]:
    """创建全新普通用户，返回 (headers, user_id)"""
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    r = client.get(f"{USERS_URL}/me", headers=headers)
    assert r.status_code == 200, r.text
    return headers, r.json()["id"]


def create_department(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    *,
    name: str | None = None,
    description: str | None = None,
) -> dict:
    r = client.post(
        f"{OKR_URL}/departments",
        headers=superuser_token_headers,
        json={"name": name or random_name("dept"), "description": description},
    )
    assert r.status_code == 200, r.text
    return r.json()


def create_objective(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    *,
    title: str | None = None,
    description: str | None = None,
) -> dict:
    r = client.post(
        f"{OKR_URL}/objectives",
        headers=superuser_token_headers,
        json={"title": title or random_name("obj"), "description": description},
    )
    assert r.status_code == 200, r.text
    return r.json()


def create_kr(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    *,
    objective_id: str,
    assignee_id: str,
    start_date: date,
    deadline: date,
    progress: int = 0,
    title: str | None = None,
) -> dict:
    r = client.post(
        f"{OKR_URL}/krs",
        headers=superuser_token_headers,
        json={
            "objective_id": objective_id,
            "assignee_id": assignee_id,
            "title": title or random_name("kr"),
            "start_date": start_date.isoformat(),
            "deadline": deadline.isoformat(),
            "progress": progress,
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def set_user_department(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    *,
    user_id: str,
    department_id: str | None,
) -> None:
    """通过超管 PATCH /users/{id} 调整成员所属部门"""
    r = client.patch(
        f"{USERS_URL}/{user_id}",
        headers=superuser_token_headers,
        json={"department_id": department_id},
    )
    assert r.status_code == 200, r.text


def get_objective(
    client: TestClient, superuser_token_headers: dict[str, str], objective_id: str
) -> dict:
    """OKR 没有单查端点，从列表里捞"""
    r = client.get(f"{OKR_URL}/objectives", headers=superuser_token_headers)
    assert r.status_code == 200, r.text
    for obj in r.json()["data"]:
        if obj["id"] == objective_id:
            return obj
    raise AssertionError(f"objective {objective_id} not found in list")
