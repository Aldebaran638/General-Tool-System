from datetime import date, datetime, time, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.modules.workbench.work_report.models import (
    WorkReport,
    WorkReportReminderDelivery,
    WorkReportReminderRule,
    WorkReportReminderRuleRecipient,
    WorkReportReminderRun,
)
from app.modules.workbench.work_report.reminder_service import (
    _due_occurrence,
    _matches_date,
    dispatch_rule,
)
from tests.utils.user import create_random_user

URL = f"{settings.API_V1_STR}/work-reports"


def test_reminder_rule_admin_api(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    recipient = create_random_user(db)
    recipient.feishu_open_id = "ou_rule_admin_recipient"
    db.add(recipient)
    db.commit()
    payload = {
        "report_type": "weekly",
        "weekday": 5,
        "month_day": None,
        "is_last_day": False,
        "local_time": "16:41",
        "timezone": "Asia/Shanghai",
        "enabled": True,
        "recipient_user_ids": [str(recipient.id)],
    }
    forbidden = client.post(
        f"{URL}/reminder-rules",
        headers=normal_user_token_headers,
        json=payload,
    )
    assert forbidden.status_code == 403

    created = client.post(
        f"{URL}/reminder-rules",
        headers=superuser_token_headers,
        json=payload,
    )
    assert created.status_code == 201, created.text
    rule = created.json()
    assert rule["report_type"] == "weekly"
    assert rule["weekday"] == 5

    duplicate = client.post(
        f"{URL}/reminder-rules",
        headers=superuser_token_headers,
        json=payload,
    )
    assert duplicate.status_code == 409

    payload.update(
        {
            "report_type": "monthly",
            "weekday": None,
            "month_day": None,
            "is_last_day": True,
            "local_time": "18:42",
            "timezone": "Europe/London",
        }
    )
    updated = client.put(
        f"{URL}/reminder-rules/{rule['id']}",
        headers=superuser_token_headers,
        json=payload,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["is_last_day"] is True

    deleted = client.delete(
        f"{URL}/reminder-rules/{rule['id']}",
        headers=superuser_token_headers,
    )
    assert deleted.status_code == 200


def test_rule_validation_rejects_invalid_combinations(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{URL}/reminder-rules",
        headers=superuser_token_headers,
        json={
            "report_type": "weekly",
            "weekday": None,
            "month_day": 10,
            "is_last_day": False,
            "local_time": "17:43",
            "timezone": "Not/AZone",
        },
    )
    assert response.status_code == 422


def test_rule_validation_rejects_unbound_recipient(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    unbound = create_random_user(db)
    response = client.post(
        f"{URL}/reminder-rules",
        headers=superuser_token_headers,
        json={
            "report_type": "weekly",
            "weekday": 2,
            "month_day": None,
            "is_last_day": False,
            "local_time": "15:37",
            "timezone": "Asia/Shanghai",
            "enabled": True,
            "recipient_user_ids": [str(unbound.id)],
        },
    )
    assert response.status_code == 422


def test_rule_list_keeps_legacy_rule_without_recipients_visible(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    legacy_rule = WorkReportReminderRule(
        report_type="weekly",
        weekday=3,
        local_time=time(13, 36),
        timezone="Asia/Shanghai",
        schedule_signature="legacy-without-recipients",
    )
    db.add(legacy_rule)
    db.commit()
    db.refresh(legacy_rule)

    response = client.get(
        f"{URL}/reminder-rules",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200, response.text
    rules = {item["id"]: item for item in response.json()["data"]}
    assert rules[str(legacy_rule.id)]["recipient_user_ids"] == []


def test_monthly_schedule_clamps_short_month_and_last_day() -> None:
    fixed = WorkReportReminderRule(
        report_type="monthly",
        month_day=31,
        is_last_day=False,
        local_time=time(17),
        timezone="Asia/Shanghai",
        schedule_signature="test-fixed",
    )
    assert _matches_date(fixed, date(2028, 2, 29))
    assert not _matches_date(fixed, date(2028, 2, 28))

    last = WorkReportReminderRule(
        report_type="monthly",
        is_last_day=True,
        local_time=time(17),
        timezone="Asia/Shanghai",
        schedule_signature="test-last",
    )
    assert _matches_date(last, date(2026, 4, 30))
    occurrence = _due_occurrence(
        last,
        datetime(2026, 4, 30, 9, 30, tzinfo=timezone.utc),
    )
    assert occurrence == datetime(2026, 4, 30, 9, 0, tzinfo=timezone.utc)


def test_dispatch_only_unsubmitted_bound_users_and_is_idempotent(
    db: Session,
) -> None:
    target = create_random_user(db)
    target.full_name = "Reminder Target"
    target.feishu_open_id = "ou-reminder-target"
    submitted = create_random_user(db)
    submitted.feishu_open_id = "ou-reminder-submitted"
    unbound = create_random_user(db)
    not_selected = create_random_user(db)
    not_selected.feishu_open_id = "ou-reminder-not-selected"
    db.add_all([target, submitted, unbound, not_selected])
    db.commit()

    db.add(
        WorkReport(
            reporter_id=submitted.id,
            reporter_name=submitted.full_name,
            reporter_email=str(submitted.email),
            report_type="weekly",
            period_start=date(2026, 7, 20),
            period_end=date(2026, 7, 26),
            title="Already submitted",
        )
    )
    rule = WorkReportReminderRule(
        report_type="weekly",
        weekday=5,
        local_time=time(17, 44),
        timezone="Asia/Shanghai",
        schedule_signature="weekly:weekday:5:17:44:Asia/Shanghai-test",
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    db.add_all(
        [
            WorkReportReminderRuleRecipient(
                rule_id=rule.id,
                user_id=user.id,
            )
            for user in (target, submitted, unbound)
        ]
    )
    db.commit()

    scheduled_for = datetime(2026, 7, 24, 9, 44, tzinfo=timezone.utc)
    with patch(
        "app.modules.workbench.work_report.reminder_service.send_interactive_message",
        return_value="om_test",
    ) as send:
        dispatch_rule(
            session=db,
            rule=rule,
            scheduled_for=scheduled_for,
        )
        first_call_count = send.call_count
        dispatch_rule(
            session=db,
            rule=rule,
            scheduled_for=scheduled_for,
        )
        assert send.call_count == first_call_count

    run = db.exec(
        select(WorkReportReminderRun).where(
            WorkReportReminderRun.rule_id == rule.id,
            WorkReportReminderRun.scheduled_for == scheduled_for,
        )
    ).one()
    deliveries = db.exec(
        select(WorkReportReminderDelivery).where(
            WorkReportReminderDelivery.run_id == run.id
        )
    ).all()
    delivered_user_ids = {item.user_id for item in deliveries}
    assert target.id in delivered_user_ids
    assert submitted.id not in delivered_user_ids
    assert unbound.id in delivered_user_ids
    assert not_selected.id not in delivered_user_ids
    status_by_user = {item.user_id: item.status for item in deliveries}
    assert status_by_user[target.id] == "sent"
    assert status_by_user[unbound.id] == "skipped"


def test_unbound_users_endpoint_lists_active_unlinked_user(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    user = create_random_user(db)
    user.full_name = "Unbound Reminder User"
    db.add(user)
    db.commit()

    response = client.get(
        f"{URL}/reminder-unbound-users",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200, response.text
    ids = {item["id"] for item in response.json()["data"]}
    assert str(user.id) in ids


def test_rule_recipients_only_lists_active_feishu_users(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    linked = create_random_user(db)
    linked.feishu_open_id = "ou_rule_recipient_list"
    unbound = create_random_user(db)
    db.add_all([linked, unbound])
    db.commit()

    response = client.get(
        f"{URL}/reminder-recipients",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200, response.text
    recipients = {item["id"]: item for item in response.json()["data"]}
    assert str(linked.id) in recipients
    assert recipients[str(linked.id)]["department_id"] == (
        str(linked.department_id) if linked.department_id else None
    )
    assert str(unbound.id) not in recipients


def test_reminder_test_sends_only_to_selected_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    recipient = create_random_user(db)
    recipient.full_name = "Selected Test Recipient"
    recipient.feishu_open_id = "ou_selected_test_recipient"
    db.add(recipient)
    db.commit()

    with patch(
        "app.modules.workbench.work_report.reminder_service.send_interactive_message",
        return_value="om_test",
    ) as send_mock:
        recipients = client.get(
            f"{URL}/reminder-test-recipients",
            headers=superuser_token_headers,
        )
        assert recipients.status_code == 200, recipients.text
        assert str(recipient.id) in {
            item["id"] for item in recipients.json()["data"]
        }

        response = client.post(
            f"{URL}/reminder-test",
            headers=superuser_token_headers,
            json={"user_id": str(recipient.id)},
        )
        assert response.status_code == 200, response.text
        assert response.json()["message_id"] == "om_test"
        send_mock.assert_called_once()
        assert send_mock.call_args.kwargs["open_id"] == recipient.feishu_open_id


def test_reminder_test_rejects_unbound_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    recipient = create_random_user(db)
    recipient.feishu_open_id = None
    db.add(recipient)
    db.commit()

    response = client.post(
        f"{URL}/reminder-test",
        headers=superuser_token_headers,
        json={"user_id": str(recipient.id)},
    )
    assert response.status_code == 400
