import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app.core.config import settings
from app.models_core import User
from app.modules.workbench.work_report.models import (
    TaskSummary,
    WorkPlan,
    WorkReport,
    WorkReview,
)
from app.modules.workbench.work_report.schemas import WorkReportSubmit
from app.modules.workbench.work_report.service import submit_work_report
from tests.modules.okr.helpers import new_user_headers, random_name

URL = f"{settings.API_V1_STR}/work-reports"


def _payload(period_key: str, *, title: str | None = None) -> dict:
    return {
        "report_type": "weekly",
        "period_key": period_key,
        "title": title or random_name("weekly-report"),
        "remarks": "本周备注",
        "work_plans": [
            {
                "plan_content": "完成下周方案",
                "planned_completion_date": "2026-08-03",
                "expected_result": "通过评审",
            }
        ],
        "task_summaries": [
            {
                "work_goal": "完成接口开发",
                "completion_date": "2026-07-31",
                "progress_description": "主要接口已完成",
                "progress": 80,
                "incomplete_reason": "等待联调",
            }
        ],
        "work_reviews": [
            {"review_module": "协作", "review_content": "需求确认应更早进行"}
        ],
    }


def test_field_config_defaults(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.get(f"{URL}/field-config", headers=normal_user_token_headers)
    assert response.status_code == 200, response.text
    configs = {
        (item["section"], item["field_key"]): item["is_required"]
        for item in response.json()["data"]
    }
    assert len(configs) == 12
    assert configs[("work_plan", "plan_content")] is True
    assert configs[("work_plan", "support_needed")] is False
    assert configs[("task_summary", "progress")] is True


def test_non_superuser_cannot_update_config(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    configs = client.get(
        f"{URL}/field-config", headers=normal_user_token_headers
    ).json()
    response = client.put(
        f"{URL}/field-config",
        headers=normal_user_token_headers,
        json=configs,
    )
    assert response.status_code == 403


def test_create_report_uses_current_user_and_all_details(
    client: TestClient, db: Session
) -> None:
    headers, user_id = new_user_headers(client, db)
    payload = _payload("2026-W31")
    payload["reporter_id"] = "00000000-0000-0000-0000-000000000000"
    rejected = client.post(URL, headers=headers, json=payload)
    assert rejected.status_code == 422

    payload.pop("reporter_id")
    response = client.post(URL, headers=headers, json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["submission_mode"] == "created"
    assert data["reporter"]["id"] == user_id
    assert data["period_start"] == "2026-07-27"
    assert data["period_end"] == "2026-08-02"
    assert data["counts"] == {
        "work_plans": 1,
        "task_summaries": 1,
        "work_reviews": 1,
    }

    report = db.get(WorkReport, data["id"])
    assert report is not None
    assert str(report.reporter_id) == user_id
    assert db.exec(
        select(func.count()).select_from(WorkPlan).where(
            WorkPlan.work_report_id == report.id
        )
    ).one() == 1


def test_same_period_supplements_existing_report(
    client: TestClient, db: Session
) -> None:
    headers, user_id = new_user_headers(client, db)
    first = client.post(URL, headers=headers, json=_payload("2026-W32"))
    assert first.status_code == 201, first.text
    new_title = random_name("supplemented")
    second = client.post(
        URL, headers=headers, json=_payload("2026-W32", title=new_title)
    )
    assert second.status_code == 201, second.text
    data = second.json()
    assert data["id"] == first.json()["id"]
    assert data["submission_mode"] == "supplemented"
    assert data["title"] == new_title
    assert data["counts"] == {
        "work_plans": 2,
        "task_summaries": 2,
        "work_reviews": 2,
    }
    reports = db.exec(
        select(WorkReport).where(
            WorkReport.reporter_id == uuid.UUID(user_id),
            WorkReport.period_start == date(2026, 8, 3),
        )
    ).all()
    assert len(reports) == 1


def test_empty_sections_are_allowed(client: TestClient, db: Session) -> None:
    headers, _ = new_user_headers(client, db)
    response = client.post(
        URL,
        headers=headers,
        json={
            "report_type": "monthly",
            "period_key": "2026-09",
            "title": "九月月报",
            "work_plans": [],
            "task_summaries": [],
            "work_reviews": [],
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["counts"] == {
        "work_plans": 0,
        "task_summaries": 0,
        "work_reviews": 0,
    }


def test_required_and_incomplete_validation(
    client: TestClient, db: Session
) -> None:
    headers, _ = new_user_headers(client, db)
    response = client.post(
        URL,
        headers=headers,
        json={
            "report_type": "weekly",
            "period_key": "2026-W34",
            "title": "校验周报",
            "work_plans": [{"support_needed": "需要支持"}],
            "task_summaries": [
                {
                    "work_goal": "目标",
                    "progress_description": "进行中",
                    "progress": 50,
                }
            ],
            "work_reviews": [],
        },
    )
    assert response.status_code == 422
    errors = response.json()["detail"]["validation_errors"]
    assert any(item["field"] == "plan_content" for item in errors)
    assert any(item["field"] == "incomplete_reason" for item in errors)
    assert db.exec(
        select(func.count()).select_from(WorkReport).where(
            WorkReport.title == "校验周报"
        )
    ).one() == 0


def test_superuser_can_update_field_config(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    configs = client.get(
        f"{URL}/field-config", headers=superuser_token_headers
    ).json()["data"]
    for item in configs:
        if item["section"] == "work_plan" and item["field_key"] == "support_needed":
            item["is_required"] = True
    response = client.put(
        f"{URL}/field-config",
        headers=superuser_token_headers,
        json={"data": configs},
    )
    assert response.status_code == 200, response.text
    updated = {
        (item["section"], item["field_key"]): item["is_required"]
        for item in response.json()["data"]
    }
    assert updated[("work_plan", "support_needed")] is True

    for item in configs:
        if item["section"] == "work_plan" and item["field_key"] == "support_needed":
            item["is_required"] = False
    restored = client.put(
        f"{URL}/field-config",
        headers=superuser_token_headers,
        json={"data": configs},
    )
    assert restored.status_code == 200


def test_deleting_reporter_keeps_snapshot(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    headers, user_id = new_user_headers(client, db)
    response = client.post(URL, headers=headers, json=_payload("2026-W35"))
    assert response.status_code == 201, response.text
    report_id = response.json()["id"]
    reporter_email = response.json()["reporter"]["email"]

    deleted = client.delete(
        f"{settings.API_V1_STR}/users/{user_id}", headers=superuser_token_headers
    )
    assert deleted.status_code == 200, deleted.text
    db.expire_all()
    report = db.get(WorkReport, report_id)
    assert report is not None
    assert report.reporter_id is None
    assert report.reporter_email == reporter_email
    assert db.exec(
        select(func.count()).select_from(TaskSummary).where(
            TaskSummary.work_report_id == report.id
        )
    ).one() == 1
    assert db.exec(
        select(func.count()).select_from(WorkReview).where(
            WorkReview.work_report_id == report.id
        )
    ).one() == 1


def test_transaction_rolls_back_when_commit_fails(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, user_id = new_user_headers(client, db)
    user = db.get(User, uuid.UUID(user_id))
    assert user is not None
    payload = WorkReportSubmit.model_validate(
        _payload("2026-W36", title="应完整回滚的汇报")
    )

    with monkeypatch.context() as patcher:
        patcher.setattr(
            db,
            "commit",
            lambda: (_ for _ in ()).throw(RuntimeError("simulated commit failure")),
        )
        with pytest.raises(RuntimeError, match="simulated commit failure"):
            submit_work_report(session=db, payload=payload, current_user=user)

    assert db.exec(
        select(func.count()).select_from(WorkReport).where(
            WorkReport.title == "应完整回滚的汇报"
        )
    ).one() == 0


def test_my_history_only_returns_current_users_reports(
    client: TestClient, db: Session
) -> None:
    first_headers, first_user_id = new_user_headers(client, db)
    second_headers, _ = new_user_headers(client, db)
    first_title = random_name("mine-history")
    second_title = random_name("other-history")
    first = client.post(
        URL,
        headers=first_headers,
        json=_payload("2026-W37", title=first_title),
    )
    second = client.post(
        URL,
        headers=second_headers,
        json=_payload("2026-W37", title=second_title),
    )
    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        f"{URL}/mine",
        headers=first_headers,
        params={"keyword": "mine-history", "report_type": "weekly"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["title"] == first_title
    assert data["data"][0]["reporter"]["id"] == first_user_id
    assert data["data"][0]["counts"] == {
        "work_plans": 1,
        "task_summaries": 1,
        "work_reviews": 1,
    }


def test_admin_history_supports_reporter_and_date_filters(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    headers, _ = new_user_headers(client, db)
    me = client.get(f"{settings.API_V1_STR}/users/me", headers=headers).json()
    title = random_name("admin-filter")
    created = client.post(
        URL, headers=headers, json=_payload("2026-W38", title=title)
    )
    assert created.status_code == 201

    response = client.get(
        f"{URL}/admin",
        headers=superuser_token_headers,
        params={
            "reporter": me["email"],
            "period_from": "2026-09-14",
            "period_to": "2026-09-20",
            "keyword": "admin-filter",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["count"] == 1
    assert response.json()["data"][0]["title"] == title

    forbidden = client.get(f"{URL}/admin", headers=headers)
    assert forbidden.status_code == 403


def test_report_detail_enforces_owner_or_admin(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    owner_headers, _ = new_user_headers(client, db)
    other_headers, _ = new_user_headers(client, db)
    created = client.post(
        URL,
        headers=owner_headers,
        json=_payload("2026-W39", title=random_name("detail")),
    )
    assert created.status_code == 201
    report_id = created.json()["id"]

    owner_response = client.get(f"{URL}/{report_id}", headers=owner_headers)
    assert owner_response.status_code == 200, owner_response.text
    assert len(owner_response.json()["work_plans"]) == 1
    assert len(owner_response.json()["task_summaries"]) == 1
    assert len(owner_response.json()["work_reviews"]) == 1

    forbidden = client.get(f"{URL}/{report_id}", headers=other_headers)
    assert forbidden.status_code == 403

    admin_response = client.get(
        f"{URL}/{report_id}", headers=superuser_token_headers
    )
    assert admin_response.status_code == 200
