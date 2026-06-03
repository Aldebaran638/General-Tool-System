"""
Tests for the admin exam management router  (/api/v1/exams/*)
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import User, UserCreate
from app.crud import create_user
from tests.utils.utils import random_lower_string


API = f"{settings.API_V1_STR}/exams"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _future_start() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()


def _future_end() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()


def _exam_payload(**overrides) -> dict:
    """Return a valid ExamCreate payload with optional overrides."""
    base = {
        "name": f"Test Exam {random_lower_string()[:8]}",
        "description": "A test exam",
        "start_at": _future_start(),
        "end_at": _future_end(),
        "duration_minutes": 60,
        "attempt_limit_type": "UNLIMITED",
        "pass_score": 10.0,
        "submit_rule": "ALL_REQUIRED",
        "show_answer": False,
        "random_question_order": False,
        "random_option_order": False,
    }
    base.update(overrides)
    return base


def _paper_payload() -> dict:
    """Return a valid PaperSaveRequest payload with two single-choice questions."""
    return {
        "questions": [
            {
                "question_type": "SINGLE_CHOICE",
                "stem": "What is 1+1?",
                "score": 10.0,
                "sort_no": 1,
                "analysis": "Basic arithmetic",
                "options": [
                    {"option_key": "A", "option_text": "2", "is_correct": True, "sort_no": 1},
                    {"option_key": "B", "option_text": "3", "is_correct": False, "sort_no": 2},
                    {"option_key": "C", "option_text": "4", "is_correct": False, "sort_no": 3},
                ],
            },
            {
                "question_type": "SINGLE_CHOICE",
                "stem": "What is 2+2?",
                "score": 10.0,
                "sort_no": 2,
                "options": [
                    {"option_key": "A", "option_text": "3", "is_correct": False, "sort_no": 1},
                    {"option_key": "B", "option_text": "4", "is_correct": True, "sort_no": 2},
                ],
            },
        ]
    }


def _create_exam(client: TestClient, headers: dict, **overrides) -> dict:
    """Create an exam and return the response JSON."""
    r = client.post(API, headers=headers, json=_exam_payload(**overrides))
    assert r.status_code == 201, r.text
    return r.json()


def _create_and_publish_exam(
    client: TestClient, headers: dict, session: Session, db_user: User
) -> dict:
    """Create an exam, save paper, add a participant, publish, and return the exam JSON."""
    exam = _create_exam(client, headers)
    exam_id = exam["id"]

    # Save paper
    r = client.put(f"{API}/{exam_id}/paper", headers=headers, json=_paper_payload())
    assert r.status_code == 204, r.text

    # Add participant by user id
    r = client.post(
        f"{API}/{exam_id}/participants/by-users",
        headers=headers,
        json={"userids": [str(db_user.id)]},
    )
    assert r.status_code == 200, r.text

    # Publish
    r = client.post(f"{API}/{exam_id}/publish", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


# ─── CRUD Tests ───────────────────────────────────────────────────────────────

class TestExamCRUD:

    def test_create_exam(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        payload = _exam_payload()
        r = client.post(API, headers=superuser_token_headers, json=payload)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["name"] == payload["name"]
        assert data["status"] == "DRAFT"
        assert "id" in data

    def test_create_exam_minimal_fields(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Create with only required fields (defaults kick in)."""
        payload = {
            "name": "Minimal Exam",
            "start_at": _future_start(),
            "end_at": _future_end(),
            "duration_minutes": 30,
            "pass_score": 50.0,
        }
        r = client.post(API, headers=superuser_token_headers, json=payload)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["attempt_limit_type"] == "UNLIMITED"
        assert data["submit_rule"] == "ALL_REQUIRED"
        assert data["show_answer"] is False

    def test_list_exams(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        # Create at least one exam
        _create_exam(client, superuser_token_headers)
        r = client.get(API, headers=superuser_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "data" in data
        assert "count" in data
        assert isinstance(data["data"], list)
        assert data["count"] >= 1

    def test_list_exams_with_pagination(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        r = client.get(API, headers=superuser_token_headers, params={"page": 1, "limit": 5})
        assert r.status_code == 200, r.text
        data = r.json()
        assert len(data["data"]) <= 5

    def test_list_exams_filter_by_status(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        r = client.get(API, headers=superuser_token_headers, params={"status": "DRAFT"})
        assert r.status_code == 200, r.text

    def test_list_exams_search_by_name(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        _create_exam(client, superuser_token_headers, name="UniqueSearchableExam123")
        r = client.get(API, headers=superuser_token_headers, params={"q": "UniqueSearchable"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["count"] >= 1

    def test_get_exam(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        r = client.get(f"{API}/{exam['id']}", headers=superuser_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["id"] == exam["id"]
        assert data["name"] == exam["name"]

    def test_get_exam_not_found(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        fake_id = str(uuid.uuid4())
        r = client.get(f"{API}/{fake_id}", headers=superuser_token_headers)
        assert r.status_code == 404

    def test_update_exam(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        update_payload = {"name": "Updated Exam Name"}
        r = client.put(
            f"{API}/{exam['id']}", headers=superuser_token_headers, json=update_payload
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["name"] == "Updated Exam Name"

    def test_update_exam_not_found(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        fake_id = str(uuid.uuid4())
        r = client.put(
            f"{API}/{fake_id}", headers=superuser_token_headers, json={"name": "Nope"}
        )
        assert r.status_code == 404

    def test_update_published_exam_fails(
        self, client: TestClient, superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str], db: Session,
    ) -> None:
        """Cannot update a published exam (service raises ValueError)."""
        exam = _create_exam(client, superuser_token_headers)
        exam_id = exam["id"]

        # Save paper + add real participant + publish
        client.put(f"{API}/{exam_id}/paper", headers=superuser_token_headers, json=_paper_payload())
        from app.core.config import settings as cfg
        from app.crud import get_user_by_email
        test_user = get_user_by_email(session=db, email=cfg.EMAIL_TEST_USER)
        client.post(
            f"{API}/{exam_id}/participants/by-users",
            headers=superuser_token_headers,
            json={"userids": [str(test_user.id)]},
        )
        r = client.post(f"{API}/{exam_id}/publish", headers=superuser_token_headers)
        assert r.status_code == 200, r.text

        # Try to update published exam
        r = client.put(
            f"{API}/{exam_id}", headers=superuser_token_headers, json={"name": "Should Fail"}
        )
        assert r.status_code == 400
        assert "只能编辑未发布的考试" in r.json()["detail"]

    def test_delete_exam(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        r = client.delete(f"{API}/{exam['id']}", headers=superuser_token_headers)
        assert r.status_code == 204

        # Verify it's gone
        r = client.get(f"{API}/{exam['id']}", headers=superuser_token_headers)
        assert r.status_code == 404

    def test_delete_exam_not_found(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        fake_id = str(uuid.uuid4())
        r = client.delete(f"{API}/{fake_id}", headers=superuser_token_headers)
        assert r.status_code == 404


# ─── Paper Tests ──────────────────────────────────────────────────────────────

class TestExamPaper:

    def test_save_paper(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        paper = _paper_payload()
        r = client.put(
            f"{API}/{exam['id']}/paper", headers=superuser_token_headers, json=paper
        )
        assert r.status_code == 204, r.text

    def test_save_paper_exam_not_found(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        fake_id = str(uuid.uuid4())
        r = client.put(
            f"{API}/{fake_id}/paper", headers=superuser_token_headers, json=_paper_payload()
        )
        assert r.status_code == 404

    def test_get_paper(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        client.put(
            f"{API}/{exam['id']}/paper", headers=superuser_token_headers, json=_paper_payload()
        )
        r = client.get(f"{API}/{exam['id']}/paper", headers=superuser_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "questions" in data
        assert data["question_count"] == 2
        assert data["total_score"] == 20.0
        assert len(data["questions"]) == 2
        # Verify options are present
        for q in data["questions"]:
            assert "options" in q
            assert len(q["options"]) >= 2

    def test_get_paper_empty(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Get paper for an exam with no questions saved yet."""
        exam = _create_exam(client, superuser_token_headers)
        r = client.get(f"{API}/{exam['id']}/paper", headers=superuser_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["questions"] == []
        assert data["total_score"] == 0.0
        assert data["question_count"] == 0

    def test_save_paper_replaces_existing(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Saving paper again replaces old questions."""
        exam = _create_exam(client, superuser_token_headers)
        exam_id = exam["id"]

        # Save initial paper (2 questions)
        client.put(f"{API}/{exam_id}/paper", headers=superuser_token_headers, json=_paper_payload())

        # Save new paper (1 question)
        new_paper = {
            "questions": [
                {
                    "question_type": "SINGLE_CHOICE",
                    "stem": "New question",
                    "score": 20.0,
                    "sort_no": 1,
                    "options": [
                        {"option_key": "A", "option_text": "Yes", "is_correct": True, "sort_no": 1},
                        {"option_key": "B", "option_text": "No", "is_correct": False, "sort_no": 2},
                    ],
                }
            ]
        }
        r = client.put(f"{API}/{exam_id}/paper", headers=superuser_token_headers, json=new_paper)
        assert r.status_code == 204, r.text

        r = client.get(f"{API}/{exam_id}/paper", headers=superuser_token_headers)
        data = r.json()
        assert data["question_count"] == 1
        assert data["total_score"] == 20.0


# ─── Lifecycle Tests ──────────────────────────────────────────────────────────

class TestExamLifecycle:

    def test_validate_exam(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        exam_id = exam["id"]

        # Save paper
        client.put(f"{API}/{exam_id}/paper", headers=superuser_token_headers, json=_paper_payload())

        # Add a participant
        client.post(
            f"{API}/{exam_id}/participants/by-users",
            headers=superuser_token_headers,
            json={"userids": [str(uuid.uuid4())]},  # won't match real users
        )

        r = client.post(f"{API}/{exam_id}/validate", headers=superuser_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "valid" in data
        assert "errors" in data

    def test_validate_exam_missing_questions(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        r = client.post(f"{API}/{exam['id']}/validate", headers=superuser_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["valid"] is False
        # Should have error about needing questions and participants
        assert any("题" in e for e in data["errors"])

    def test_publish_exam(
        self, client: TestClient, superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str], db: Session,
    ) -> None:
        """Publish an exam that has paper and participants."""
        exam = _create_exam(client, superuser_token_headers)
        exam_id = exam["id"]

        # Save paper
        client.put(f"{API}/{exam_id}/paper", headers=superuser_token_headers, json=_paper_payload())

        # Add participant by user UUID (use the test user from normal_user_token_headers)
        from app.core.config import settings as cfg
        from app.crud import get_user_by_email
        test_user = get_user_by_email(session=db, email=cfg.EMAIL_TEST_USER)
        assert test_user is not None

        r = client.post(
            f"{API}/{exam_id}/participants/by-users",
            headers=superuser_token_headers,
            json={"userids": [str(test_user.id)]},
        )
        assert r.status_code == 200, r.text

        # Publish
        r = client.post(f"{API}/{exam_id}/publish", headers=superuser_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "PUBLISHED"
        assert data["published_at"] is not None

    def test_publish_exam_not_found(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        fake_id = str(uuid.uuid4())
        r = client.post(f"{API}/{fake_id}/publish", headers=superuser_token_headers)
        assert r.status_code == 404

    def test_publish_exam_validation_failure(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Publishing without questions and participants should fail."""
        exam = _create_exam(client, superuser_token_headers)
        r = client.post(f"{API}/{exam['id']}/publish", headers=superuser_token_headers)
        assert r.status_code == 400
        assert "发布校验失败" in r.json()["detail"]

    def test_archive_exam(
        self, client: TestClient, superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        exam_id = exam["id"]

        # Set up and publish
        client.put(f"{API}/{exam_id}/paper", headers=superuser_token_headers, json=_paper_payload())
        from app.core.config import settings as cfg
        from app.crud import get_user_by_email
        test_user = get_user_by_email(session=db, email=cfg.EMAIL_TEST_USER)
        client.post(
            f"{API}/{exam_id}/participants/by-users",
            headers=superuser_token_headers,
            json={"userids": [str(test_user.id)]},
        )
        client.post(f"{API}/{exam_id}/publish", headers=superuser_token_headers)

        # Archive
        r = client.post(f"{API}/{exam_id}/archive", headers=superuser_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "ARCHIVED"

    def test_archive_draft_exam_fails(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Cannot archive a DRAFT exam."""
        exam = _create_exam(client, superuser_token_headers)
        r = client.post(f"{API}/{exam['id']}/archive", headers=superuser_token_headers)
        assert r.status_code == 400

    def test_delete_published_exam_fails(
        self, client: TestClient, superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Cannot delete a PUBLISHED exam."""
        exam = _create_exam(client, superuser_token_headers)
        exam_id = exam["id"]

        client.put(f"{API}/{exam_id}/paper", headers=superuser_token_headers, json=_paper_payload())
        from app.core.config import settings as cfg
        from app.crud import get_user_by_email
        test_user = get_user_by_email(session=db, email=cfg.EMAIL_TEST_USER)
        client.post(
            f"{API}/{exam_id}/participants/by-users",
            headers=superuser_token_headers,
            json={"userids": [str(test_user.id)]},
        )
        client.post(f"{API}/{exam_id}/publish", headers=superuser_token_headers)

        r = client.delete(f"{API}/{exam_id}", headers=superuser_token_headers)
        assert r.status_code == 400
        assert "已发布" in r.json()["detail"] or "不能删除" in r.json()["detail"]


# ─── Participant Tests ────────────────────────────────────────────────────────

class TestParticipants:

    def test_list_participants_empty(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        r = client.get(
            f"{API}/{exam['id']}/participants", headers=superuser_token_headers
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["data"] == []
        assert data["count"] == 0

    def test_add_participants_by_users(
        self, client: TestClient, superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        exam_id = exam["id"]

        from app.core.config import settings as cfg
        from app.crud import get_user_by_email
        test_user = get_user_by_email(session=db, email=cfg.EMAIL_TEST_USER)

        r = client.post(
            f"{API}/{exam_id}/participants/by-users",
            headers=superuser_token_headers,
            json={"userids": [str(test_user.id)]},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["added"] >= 1

    def test_add_participants_by_users_duplicate_skipped(
        self, client: TestClient, superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Adding the same user twice should only add once."""
        exam = _create_exam(client, superuser_token_headers)
        exam_id = exam["id"]

        from app.core.config import settings as cfg
        from app.crud import get_user_by_email
        test_user = get_user_by_email(session=db, email=cfg.EMAIL_TEST_USER)
        userid = str(test_user.id)

        r1 = client.post(
            f"{API}/{exam_id}/participants/by-users",
            headers=superuser_token_headers,
            json={"userids": [userid]},
        )
        assert r1.json()["added"] >= 1

        r2 = client.post(
            f"{API}/{exam_id}/participants/by-users",
            headers=superuser_token_headers,
            json={"userids": [userid]},
        )
        assert r2.json()["added"] == 0

    def test_list_participants_after_adding(
        self, client: TestClient, superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        exam_id = exam["id"]

        from app.core.config import settings as cfg
        from app.crud import get_user_by_email
        test_user = get_user_by_email(session=db, email=cfg.EMAIL_TEST_USER)

        client.post(
            f"{API}/{exam_id}/participants/by-users",
            headers=superuser_token_headers,
            json={"userids": [str(test_user.id)]},
        )

        r = client.get(
            f"{API}/{exam_id}/participants", headers=superuser_token_headers
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["count"] >= 1
        assert len(data["data"]) >= 1

    def test_list_participants_with_search(
        self, client: TestClient, superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        exam_id = exam["id"]

        from app.core.config import settings as cfg
        from app.crud import get_user_by_email
        test_user = get_user_by_email(session=db, email=cfg.EMAIL_TEST_USER)

        client.post(
            f"{API}/{exam_id}/participants/by-users",
            headers=superuser_token_headers,
            json={"userids": [str(test_user.id)]},
        )

        # Search by userid substring
        r = client.get(
            f"{API}/{exam_id}/participants",
            headers=superuser_token_headers,
            params={"q": str(test_user.id)[:8]},
        )
        assert r.status_code == 200, r.text

    def test_remove_participant(
        self, client: TestClient, superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        exam_id = exam["id"]

        from app.core.config import settings as cfg
        from app.crud import get_user_by_email
        test_user = get_user_by_email(session=db, email=cfg.EMAIL_TEST_USER)
        userid = str(test_user.id)

        client.post(
            f"{API}/{exam_id}/participants/by-users",
            headers=superuser_token_headers,
            json={"userids": [userid]},
        )

        r = client.delete(
            f"{API}/{exam_id}/participants/{userid}", headers=superuser_token_headers
        )
        assert r.status_code == 204, r.text

        # Verify removed
        r = client.get(
            f"{API}/{exam_id}/participants", headers=superuser_token_headers
        )
        assert r.json()["count"] == 0

    def test_remove_participant_not_found(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        r = client.delete(
            f"{API}/{exam['id']}/participants/nonexistent_user",
            headers=superuser_token_headers,
        )
        assert r.status_code == 404

    def test_add_participants_by_centers(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        r = client.post(
            f"{API}/{exam['id']}/participants/by-centers",
            headers=superuser_token_headers,
            json={"center_ids": [99999]},  # non-existent center
        )
        assert r.status_code == 200, r.text
        assert r.json()["added"] == 0

    def test_add_participants_by_departments(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        exam = _create_exam(client, superuser_token_headers)
        r = client.post(
            f"{API}/{exam['id']}/participants/by-departments",
            headers=superuser_token_headers,
            json={"department_ids": [99999]},  # non-existent department
        )
        assert r.status_code == 200, r.text
        assert r.json()["added"] == 0

    def test_participants_exam_not_found(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        fake_id = str(uuid.uuid4())
        r = client.get(
            f"{API}/{fake_id}/participants", headers=superuser_token_headers
        )
        assert r.status_code == 404


# ─── Auth Tests ───────────────────────────────────────────────────────────────

class TestAuth:

    def test_no_auth_returns_401(self, client: TestClient) -> None:
        """All admin endpoints require authentication."""
        r = client.get(API)
        assert r.status_code == 401

    def test_normal_user_forbidden(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Non-admin users cannot access admin exam endpoints."""
        r = client.get(API, headers=normal_user_token_headers)
        assert r.status_code == 403
