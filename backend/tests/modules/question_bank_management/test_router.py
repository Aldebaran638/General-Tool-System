"""
Tests for the question bank management router (/api/v1/question-bank-management/*)
and the exam import endpoint (/api/v1/exams/{exam_id}/import-question-bank).
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import SystemUserRole, User
from app import crud
from app.models import UserCreate
from app.modules.exam_management.models import ExamParticipant
from tests.utils.utils import random_lower_string


API = f"{settings.API_V1_STR}/question-bank-management"
EXAMS_API = f"{settings.API_V1_STR}/exams"


def _future_start() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()


def _future_end() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()


def _exam_payload(**overrides) -> dict:
    base = {
        "name": f"Test Exam {random_lower_string()[:8]}",
        "start_at": _future_start(),
        "end_at": _future_end(),
        "duration_minutes": 60,
        "attempt_limit_type": "UNLIMITED",
        "pass_score": 60.0,
        "submit_rule": "ALL_REQUIRED",
        "show_answer": False,
        "random_question_order": False,
        "random_option_order": False,
    }
    base.update(overrides)
    return base


def _set_payload(**overrides) -> dict:
    base = {
        "name": f"Test Bank {random_lower_string()[:8]}",
        "description": "A test question bank",
    }
    base.update(overrides)
    return base


def _question_payload(**overrides) -> dict:
    base = {
        "question_type": "SINGLE_CHOICE",
        "stem": "What is 1+1?",
        "score": 10.0,
        "difficulty": "MEDIUM",
        "sort_no": 1,
        "analysis": "Basic arithmetic",
        "options": [
            {"option_key": "A", "option_text": "2", "is_correct": True, "sort_no": 1},
            {"option_key": "B", "option_text": "3", "is_correct": False, "sort_no": 2},
        ],
    }
    base.update(overrides)
    return base


def _create_exam(client: TestClient, headers: dict, **overrides) -> dict:
    r = client.post(EXAMS_API, headers=headers, json=_exam_payload(**overrides))
    assert r.status_code == 201, r.text
    return r.json()


def _create_set(client: TestClient, headers: dict, **overrides) -> dict:
    r = client.post(f"{API}/sets", headers=headers, json=_set_payload(**overrides))
    assert r.status_code == 201, r.text
    return r.json()


def _create_question(client: TestClient, headers: dict, set_id: str, **overrides) -> dict:
    r = client.post(
        f"{API}/sets/{set_id}/questions",
        headers=headers,
        json=_question_payload(**overrides),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _exam_admin_headers(client: TestClient, db: Session) -> dict:
    """Create a normal user with EXAM_ADMIN role and return auth headers."""
    wecom_userid = random_lower_string()
    password = random_lower_string()
    user = crud.create_user(
        session=db,
        user_create=UserCreate(wecom_userid=wecom_userid, password=password),
    )
    db.add(SystemUserRole(userid=user.wecom_userid, role_code="EXAM_ADMIN"))
    db.commit()

    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": user.wecom_userid, "password": password},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


class TestQuestionBankSetCRUD:
    def test_create_set(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        r = client.post(f"{API}/sets", headers=superuser_token_headers, json=_set_payload())
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["name"]
        assert "id" in data

    def test_list_sets(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        _create_set(client, superuser_token_headers)
        r = client.get(f"{API}/sets", headers=superuser_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "data" in data
        assert "count" in data

    def test_get_set_detail(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        bank_set = _create_set(client, superuser_token_headers)
        _create_question(client, superuser_token_headers, bank_set["id"])
        r = client.get(f"{API}/sets/{bank_set['id']}", headers=superuser_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["questions"]
        assert len(data["questions"]) == 1

    def test_update_set(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        bank_set = _create_set(client, superuser_token_headers)
        r = client.put(
            f"{API}/sets/{bank_set['id']}",
            headers=superuser_token_headers,
            json={"name": "Updated name"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["name"] == "Updated name"

    def test_delete_set(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        bank_set = _create_set(client, superuser_token_headers)
        r = client.delete(
            f"{API}/sets/{bank_set['id']}", headers=superuser_token_headers
        )
        assert r.status_code == 204, r.text
        r = client.get(f"{API}/sets/{bank_set['id']}", headers=superuser_token_headers)
        assert r.status_code == 404, r.text


class TestBankQuestionCRUD:
    def test_create_question(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        bank_set = _create_set(client, superuser_token_headers)
        q = _create_question(client, superuser_token_headers, bank_set["id"])
        assert q["set_id"] == bank_set["id"]
        assert len(q["options"]) == 2

    def test_update_question(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        bank_set = _create_set(client, superuser_token_headers)
        q = _create_question(client, superuser_token_headers, bank_set["id"])
        r = client.put(
            f"{API}/sets/{bank_set['id']}/questions/{q['id']}",
            headers=superuser_token_headers,
            json={
                **_question_payload(),
                "stem": "Updated stem",
                "options": [
                    {
                        "option_key": "A",
                        "option_text": "New answer",
                        "is_correct": True,
                        "sort_no": 1,
                    }
                ],
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["stem"] == "Updated stem"

    def test_delete_question(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        bank_set = _create_set(client, superuser_token_headers)
        q = _create_question(client, superuser_token_headers, bank_set["id"])
        r = client.delete(
            f"{API}/sets/{bank_set['id']}/questions/{q['id']}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 204, r.text


class TestImportQuestionBank:
    def test_import_overwrite(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        bank_set = _create_set(client, superuser_token_headers)
        _create_question(client, superuser_token_headers, bank_set["id"])

        r = client.post(
            f"{EXAMS_API}/{exam['id']}/import-question-bank",
            headers=superuser_token_headers,
            json={"bank_set_id": bank_set["id"], "mode": "overwrite"},
        )
        assert r.status_code == 204, r.text

        r = client.get(
            f"{EXAMS_API}/{exam['id']}/paper", headers=superuser_token_headers
        )
        paper = r.json()
        assert paper["question_count"] == 1
        assert paper["questions"][0]["stem"] == "What is 1+1?"

    def test_import_append(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        # Add one existing question to the exam via paper save
        r = client.put(
            f"{EXAMS_API}/{exam['id']}/paper",
            headers=superuser_token_headers,
            json={
                "questions": [
                    {
                        "question_type": "SINGLE_CHOICE",
                        "stem": "Existing question",
                        "score": 5.0,
                        "sort_no": 1,
                        "options": [
                            {
                                "option_key": "A",
                                "option_text": "Yes",
                                "is_correct": True,
                                "sort_no": 1,
                            }
                        ],
                    }
                ]
            },
        )
        assert r.status_code == 204, r.text

        bank_set = _create_set(client, superuser_token_headers)
        _create_question(client, superuser_token_headers, bank_set["id"])

        r = client.post(
            f"{EXAMS_API}/{exam['id']}/import-question-bank",
            headers=superuser_token_headers,
            json={"bank_set_id": bank_set["id"], "mode": "append"},
        )
        assert r.status_code == 204, r.text

        r = client.get(
            f"{EXAMS_API}/{exam['id']}/paper", headers=superuser_token_headers
        )
        paper = r.json()
        assert paper["question_count"] == 2
        sort_numbers = [q["sort_no"] for q in paper["questions"]]
        assert sorted(sort_numbers) == sort_numbers
        assert max(sort_numbers) == 2

    def test_import_to_published_exam_fails(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        bank_set = _create_set(client, superuser_token_headers)
        _create_question(
            client,
            superuser_token_headers,
            bank_set["id"],
            score=100.0,
            sort_no=1,
            options=[
                {
                    "option_key": "A",
                    "option_text": "Correct",
                    "is_correct": True,
                    "sort_no": 1,
                },
                {
                    "option_key": "B",
                    "option_text": "Wrong",
                    "is_correct": False,
                    "sort_no": 2,
                },
            ],
        )

        # Import so the exam can be published (needs 100 points and ≥1 question)
        r = client.post(
            f"{EXAMS_API}/{exam['id']}/import-question-bank",
            headers=superuser_token_headers,
            json={"bank_set_id": bank_set["id"], "mode": "overwrite"},
        )
        assert r.status_code == 204, r.text

        # Add a participant
        db.add(
            ExamParticipant(
                exam_id=uuid.UUID(exam["id"]),
                userid="test_participant",
                name_snapshot="Test Participant",
            )
        )
        db.commit()

        # Publish exam
        r = client.post(
            f"{EXAMS_API}/{exam['id']}/publish", headers=superuser_token_headers
        )
        assert r.status_code == 200, r.text

        # Importing into a published exam should fail
        r = client.post(
            f"{EXAMS_API}/{exam['id']}/import-question-bank",
            headers=superuser_token_headers,
            json={"bank_set_id": bank_set["id"], "mode": "overwrite"},
        )
        assert r.status_code == 400, r.text
        assert "未发布" in r.json()["detail"] or "DRAFT" in r.json()["detail"]


def _normal_user_headers(client: TestClient, db: Session) -> dict:
    """Create a normal user without admin role and return auth headers."""
    wecom_userid = random_lower_string()
    password = random_lower_string()
    user = crud.create_user(
        session=db,
        user_create=UserCreate(wecom_userid=wecom_userid, password=password),
    )

    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": user.wecom_userid, "password": password},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


class TestPermissions:
    def test_normal_user_cannot_access(
        self, client: TestClient, db: Session
    ) -> None:
        headers = _normal_user_headers(client, db)
        r = client.get(f"{API}/sets", headers=headers)
        assert r.status_code == 403, r.text

    def test_exam_admin_can_access(
        self, client: TestClient, db: Session
    ) -> None:
        headers = _exam_admin_headers(client, db)
        r = client.get(f"{API}/sets", headers=headers)
        assert r.status_code == 200, r.text

    def test_import_requires_admin(
        self, client: TestClient, db: Session
    ) -> None:
        headers = _normal_user_headers(client, db)
        exam_id = str(uuid.uuid4())
        r = client.post(
            f"{EXAMS_API}/{exam_id}/import-question-bank",
            headers=headers,
            json={"bank_set_id": str(uuid.uuid4()), "mode": "append"},
        )
        assert r.status_code == 403, r.text
