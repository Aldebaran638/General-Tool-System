"""
backend/tests/modules/okr/test_my_krs.py
GET /okr/krs/my?filter= 五种筛选：all / active / done / due_soon / overdue

边界约定（来自 crud.get_krs_by_assignee）：
- active：progress < 100
- done：progress >= 100
- due_soon：progress < 100 且 today <= deadline <= today+3（含两端）
- overdue：progress < 100 且 deadline < today（已到 100 即使过期也不算）
"""

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.modules.okr.helpers import (
    OKR_URL,
    create_kr,
    create_objective,
    new_user_headers,
)

URL = f"{OKR_URL}/krs/my"
TODAY = date.today()
START = TODAY - timedelta(days=10)


def _setup_krs(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> tuple[dict[str, str], dict[str, dict]]:
    """建全新用户 + 7 条覆盖各边界的 KR，返回 (用户 headers, {key: kr})"""
    headers, user_id = new_user_headers(client, db)
    obj = create_objective(client, superuser_token_headers)

    def mk(key: str, *, deadline: date, progress: int) -> dict:
        return create_kr(
            client,
            superuser_token_headers,
            objective_id=obj["id"],
            assignee_id=user_id,
            start_date=START,
            deadline=deadline,
            progress=progress,
            title=f"mykr-{key}",
        )

    krs = {
        # 进行中、离到期还远
        "active_far": mk("active_far", deadline=TODAY + timedelta(days=10), progress=10),
        # 今天到期（due_soon 下界，含）
        "due_today": mk("due_today", deadline=TODAY, progress=10),
        # 3 天后到期（due_soon 上界，含）
        "due_in_3": mk("due_in_3", deadline=TODAY + timedelta(days=3), progress=10),
        # 4 天后到期（刚好超出 due_soon 窗口）
        "due_in_4": mk("due_in_4", deadline=TODAY + timedelta(days=4), progress=10),
        # 昨天到期、未完成 → overdue
        "overdue": mk("overdue", deadline=TODAY - timedelta(days=1), progress=10),
        # 已完成、1 天后到期 → done，不算 due_soon
        "done_future": mk("done_future", deadline=TODAY + timedelta(days=1), progress=100),
        # 已完成但已过期 → done，不算 overdue
        "done_overdue": mk("done_overdue", deadline=TODAY - timedelta(days=5), progress=100),
    }
    return headers, krs


def _my_ids(client: TestClient, headers: dict[str, str], params: dict | None = None) -> list[str]:
    r = client.get(URL, headers=headers, params=params or {})
    assert r.status_code == 200, r.text
    content = r.json()
    assert content["count"] == len(content["data"])
    return [k["id"] for k in content["data"]]


def test_my_krs_filter_all(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    headers, krs = _setup_krs(client, superuser_token_headers, db)
    ids = _my_ids(client, headers, {"filter": "all"})
    assert set(ids) == {kr["id"] for kr in krs.values()}


def test_my_krs_default_filter_is_all(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    headers, krs = _setup_krs(client, superuser_token_headers, db)
    ids = _my_ids(client, headers)
    assert set(ids) == {kr["id"] for kr in krs.values()}


def test_my_krs_filter_active(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    headers, krs = _setup_krs(client, superuser_token_headers, db)
    ids = _my_ids(client, headers, {"filter": "active"})
    expected = {
        krs[k]["id"]
        for k in ("active_far", "due_today", "due_in_3", "due_in_4", "overdue")
    }
    assert set(ids) == expected


def test_my_krs_filter_done(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    headers, krs = _setup_krs(client, superuser_token_headers, db)
    ids = _my_ids(client, headers, {"filter": "done"})
    assert set(ids) == {krs["done_future"]["id"], krs["done_overdue"]["id"]}


def test_my_krs_filter_due_soon(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    headers, krs = _setup_krs(client, superuser_token_headers, db)
    ids = _my_ids(client, headers, {"filter": "due_soon"})
    # 含今天到期与今天+3 边界；排除 today+4、已过期、已完成
    assert set(ids) == {krs["due_today"]["id"], krs["due_in_3"]["id"]}
    # 结果按 deadline 升序
    assert ids == [krs["due_today"]["id"], krs["due_in_3"]["id"]]


def test_my_krs_filter_overdue(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    headers, krs = _setup_krs(client, superuser_token_headers, db)
    ids = _my_ids(client, headers, {"filter": "overdue"})
    # 已到 100 的过期 KR 不算 overdue
    assert ids == [krs["overdue"]["id"]]


def test_my_krs_only_own(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """/krs/my 只返回当前用户的 KR"""
    headers, krs = _setup_krs(client, superuser_token_headers, db)
    other_headers, _ = new_user_headers(client, db)
    ids = _my_ids(client, other_headers, {"filter": "all"})
    assert ids == []
    ids = _my_ids(client, headers, {"filter": "all"})
    assert set(ids) == {kr["id"] for kr in krs.values()}


def test_my_krs_invalid_filter_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    headers, _ = _setup_krs(client, superuser_token_headers, db)
    r = client.get(URL, headers=headers, params={"filter": "bogus"})
    assert r.status_code == 422
