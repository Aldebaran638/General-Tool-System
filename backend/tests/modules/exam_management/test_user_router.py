"""
Tests for the user-facing exam router  (/api/v1/my-exams/*)
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.crud import get_user_by_email
from tests.utils.utils import random_lower_string


API = f"{settings.API_V1_STR}/my-exams"
ADMIN_API = f"{settings.API_V1_STR}/exams"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _future_start() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()


def _future_end() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()


def _now_start() -> str:
    """A start time that is already in the past (exam is active)."""
    return (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()


def _now_end() -> str:
    """An end time far in the future (exam still open)."""
    return (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()


def _exam_payload(**overrides) -> dict:
    base = {
        "name": f"UserTest Exam {random_lower_string()[:8]}",
        "description": "A user-facing test exam",
        "start_at": _now_start(),
        "end_at": _now_end(),
        "duration_minutes": 60,
        "attempt_limit_type": "UNLIMITED",
        "pass_score": 60.0,
        "submit_rule": "ALL_REQUIRED",
        "show_answer": True,
        "random_question_order": False,
        "random_option_order": False,
    }
    base.update(overrides)
    return base


def _paper_payload() -> dict:
    return {
        "questions": [
            {
                "question_type": "SINGLE_CHOICE",
                "stem": "What is 1+1?",
                "score": 50.0,
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
                "score": 50.0,
                "sort_no": 2,
                "options": [
                    {"option_key": "A", "option_text": "3", "is_correct": False, "sort_no": 1},
                    {"option_key": "B", "option_text": "4", "is_correct": True, "sort_no": 2},
                ],
            },
        ]
    }


def _create_published_exam_for_user(
    client: TestClient,
    admin_headers: dict,
    user_id: str,
    **exam_overrides,
) -> tuple[dict, list]:
    """
    Create an exam, add paper, add participant, publish.
    Returns (exam_dict, questions_list from the paper endpoint).
    """
    # Create exam
    payload = _exam_payload(**exam_overrides)
    r = client.post(ADMIN_API, headers=admin_headers, json=payload)
    assert r.status_code == 201, r.text
    exam = r.json()
    exam_id = exam["id"]

    # Save paper
    r = client.put(f"{ADMIN_API}/{exam_id}/paper", headers=admin_headers, json=_paper_payload())
    assert r.status_code == 204, r.text

    # Add participant
    r = client.post(
        f"{ADMIN_API}/{exam_id}/participants/by-users",
        headers=admin_headers,
        json={"userids": [user_id]},
    )
    assert r.status_code == 200, r.text

    # Publish
    r = client.post(f"{ADMIN_API}/{exam_id}/publish", headers=admin_headers)
    assert r.status_code == 200, r.text
    exam = r.json()

    # Get paper for question/option IDs
    r = client.get(f"{ADMIN_API}/{exam_id}/paper", headers=admin_headers)
    assert r.status_code == 200, r.text
    paper = r.json()

    return exam, paper["questions"]


# ─── List My Exams ────────────────────────────────────────────────────────────

class TestListMyExams:

    def test_list_my_exams_empty(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """No enrolled exams returns empty list."""
        r = client.get(API, headers=normal_user_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "data" in data
        assert "count" in data
        assert isinstance(data["data"], list)

    def test_list_my_exams_after_enrollment(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """After enrolling, exam shows up in the list."""
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None

        _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id)
        )

        r = client.get(API, headers=normal_user_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["count"] >= 1

    def test_list_my_exams_pagination(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        r = client.get(API, headers=normal_user_token_headers, params={"page": 1, "limit": 5})
        assert r.status_code == 200, r.text


# ─── Get My Exam Detail ──────────────────────────────────────────────────────

class TestGetMyExam:

    def test_get_my_exam(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None

        exam, _ = _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id)
        )

        r = client.get(f"{API}/{exam['id']}", headers=normal_user_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["id"] == exam["id"]
        assert data["name"] == exam["name"]

    def test_get_my_exam_not_enrolled(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Cannot see an exam the user is not enrolled in."""
        # Create exam without enrolling the normal user
        payload = _exam_payload()
        r = client.post(ADMIN_API, headers=superuser_token_headers, json=payload)
        exam = r.json()

        r = client.get(f"{API}/{exam['id']}", headers=normal_user_token_headers)
        assert r.status_code == 404

    def test_get_my_exam_nonexistent(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        fake_id = str(uuid.uuid4())
        r = client.get(f"{API}/{fake_id}", headers=normal_user_token_headers)
        assert r.status_code == 404


# ─── Get Exam Paper ──────────────────────────────────────────────────────────

class TestGetExamPaper:

    def test_get_exam_paper(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None

        exam, _ = _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id)
        )

        r = client.get(f"{API}/{exam['id']}/paper", headers=normal_user_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "exam_id" in data
        assert "exam_name" in data
        assert "duration_minutes" in data
        assert "pass_score" in data
        assert "questions" in data
        assert len(data["questions"]) == 2

        # Verify options do NOT include is_correct (user-facing)
        for q in data["questions"]:
            for opt in q["options"]:
                assert "is_correct" not in opt

    def test_get_exam_paper_not_enrolled(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
    ) -> None:
        """Non-enrolled user gets 403."""
        payload = _exam_payload()
        r = client.post(ADMIN_API, headers=superuser_token_headers, json=payload)
        exam = r.json()

        r = client.get(f"{API}/{exam['id']}/paper", headers=normal_user_token_headers)
        assert r.status_code == 403


# ─── Start Exam ──────────────────────────────────────────────────────────────

class TestStartExam:

    def test_start_exam(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None

        exam, _ = _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id)
        )

        r = client.post(f"{API}/{exam['id']}/start", headers=normal_user_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "attempt_id" in data
        assert "started_at" in data
        assert "expire_at" in data
        assert "duration_minutes" in data
        assert data["duration_minutes"] == 60

    def test_start_exam_returns_existing_attempt(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Starting the same exam twice returns the same attempt."""
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None

        exam, _ = _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id)
        )

        r1 = client.post(f"{API}/{exam['id']}/start", headers=normal_user_token_headers)
        assert r1.status_code == 200, r1.text
        attempt_id_1 = r1.json()["attempt_id"]

        r2 = client.post(f"{API}/{exam['id']}/start", headers=normal_user_token_headers)
        assert r2.status_code == 200, r2.text
        attempt_id_2 = r2.json()["attempt_id"]

        assert attempt_id_1 == attempt_id_2

    def test_start_exam_not_enrolled(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
    ) -> None:
        payload = _exam_payload()
        r = client.post(ADMIN_API, headers=superuser_token_headers, json=payload)
        exam = r.json()

        r = client.post(f"{API}/{exam['id']}/start", headers=normal_user_token_headers)
        assert r.status_code == 403

    def test_start_exam_not_started_yet(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Cannot start an exam before its start_at time."""
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None

        exam, _ = _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id),
            start_at=(datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
            end_at=(datetime.now(timezone.utc) + timedelta(days=11)).isoformat(),
        )

        r = client.post(f"{API}/{exam['id']}/start", headers=normal_user_token_headers)
        assert r.status_code == 400
        assert "尚未开始" in r.json()["detail"]


# ─── Submit Exam ─────────────────────────────────────────────────────────────

class TestSubmitExam:

    def _start_and_get_paper(
        self, client, admin_headers, user_headers, user_id, **exam_overrides
    ):
        """Helper: create exam, start, and return (exam, paper_questions, attempt_id)."""
        exam, questions = _create_published_exam_for_user(
            client, admin_headers, user_id, **exam_overrides
        )

        # Start exam
        r = client.post(f"{API}/{exam['id']}/start", headers=user_headers)
        assert r.status_code == 200, r.text
        attempt_id = r.json()["attempt_id"]

        return exam, questions, attempt_id

    def test_submit_exam_all_correct(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None
        user_id = str(test_user.id)

        exam, questions, attempt_id = self._start_and_get_paper(
            client, superuser_token_headers, normal_user_token_headers, user_id
        )

        # Build answers: select the correct options
        answers = []
        for q in questions:
            correct_ids = [o["id"] for o in q["options"] if o.get("is_correct")]
            answers.append({
                "question_id": q["id"],
                "selected_option_ids": correct_ids,
            })

        submit_body = {"attempt_id": attempt_id, "answers": answers}
        r = client.post(
            f"{API}/{exam['id']}/submit",
            headers=normal_user_token_headers,
            json=submit_body,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["total_score"] == 100.0
        assert data["max_score"] == 100.0
        assert data["passed"] is True
        assert data["correct_count"] == 2
        assert data["total_count"] == 2

    def test_submit_exam_all_wrong(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None
        user_id = str(test_user.id)

        exam, questions, attempt_id = self._start_and_get_paper(
            client, superuser_token_headers, normal_user_token_headers, user_id
        )

        # Build answers: select wrong options
        answers = []
        for q in questions:
            wrong_ids = [o["id"] for o in q["options"] if not o.get("is_correct")]
            answers.append({
                "question_id": q["id"],
                "selected_option_ids": [wrong_ids[0]],
            })

        submit_body = {"attempt_id": attempt_id, "answers": answers}
        r = client.post(
            f"{API}/{exam['id']}/submit",
            headers=normal_user_token_headers,
            json=submit_body,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["total_score"] == 0.0
        assert data["passed"] is False
        assert data["correct_count"] == 0

    def test_submit_exam_partial_correct(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None
        user_id = str(test_user.id)

        exam, questions, attempt_id = self._start_and_get_paper(
            client, superuser_token_headers, normal_user_token_headers, user_id,
            pass_score=60.0,
        )

        # Answer first correctly, second incorrectly
        answers = []
        for i, q in enumerate(questions):
            if i == 0:
                correct_ids = [o["id"] for o in q["options"] if o.get("is_correct")]
                answers.append({"question_id": q["id"], "selected_option_ids": correct_ids})
            else:
                wrong_ids = [o["id"] for o in q["options"] if not o.get("is_correct")]
                answers.append({"question_id": q["id"], "selected_option_ids": [wrong_ids[0]]})

        submit_body = {"attempt_id": attempt_id, "answers": answers}
        r = client.post(
            f"{API}/{exam['id']}/submit",
            headers=normal_user_token_headers,
            json=submit_body,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["total_score"] == 50.0
        assert data["correct_count"] == 1
        assert data["passed"] is False  # 50 < 60 pass_score

    def test_submit_exam_missing_answers(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """ALL_REQUIRED submit rule rejects partial answers."""
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None
        user_id = str(test_user.id)

        exam, questions, attempt_id = self._start_and_get_paper(
            client, superuser_token_headers, normal_user_token_headers, user_id
        )

        # Only answer the first question
        q = questions[0]
        correct_ids = [o["id"] for o in q["options"] if o.get("is_correct")]
        answers = [{"question_id": q["id"], "selected_option_ids": correct_ids}]

        submit_body = {"attempt_id": attempt_id, "answers": answers}
        r = client.post(
            f"{API}/{exam['id']}/submit",
            headers=normal_user_token_headers,
            json=submit_body,
        )
        assert r.status_code == 400
        assert "必须回答所有" in r.json()["detail"]

    def test_submit_exam_invalid_attempt(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Submitting with a non-existent attempt_id fails."""
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None
        user_id = str(test_user.id)

        exam, questions, _ = self._start_and_get_paper(
            client, superuser_token_headers, normal_user_token_headers, user_id
        )

        submit_body = {
            "attempt_id": str(uuid.uuid4()),
            "answers": [{"question_id": questions[0]["id"], "selected_option_ids": [questions[0]["options"][0]["id"]]}],
        }
        r = client.post(
            f"{API}/{exam['id']}/submit",
            headers=normal_user_token_headers,
            json=submit_body,
        )
        assert r.status_code == 400

    def test_submit_exam_duplicate_submission(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Submitting the same attempt twice should fail on second submission."""
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None
        user_id = str(test_user.id)

        exam, questions, attempt_id = self._start_and_get_paper(
            client, superuser_token_headers, normal_user_token_headers, user_id
        )

        answers = []
        for q in questions:
            correct_ids = [o["id"] for o in q["options"] if o.get("is_correct")]
            answers.append({"question_id": q["id"], "selected_option_ids": correct_ids})

        submit_body = {"attempt_id": attempt_id, "answers": answers}

        # First submission
        r1 = client.post(
            f"{API}/{exam['id']}/submit",
            headers=normal_user_token_headers,
            json=submit_body,
        )
        assert r1.status_code == 200

        # Second submission with same attempt should fail
        r2 = client.post(
            f"{API}/{exam['id']}/submit",
            headers=normal_user_token_headers,
            json=submit_body,
        )
        assert r2.status_code == 400

    def test_submit_exam_not_enrolled(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
    ) -> None:
        """Non-enrolled user cannot submit."""
        payload = _exam_payload()
        r = client.post(ADMIN_API, headers=superuser_token_headers, json=payload)
        exam = r.json()

        submit_body = {
            "attempt_id": str(uuid.uuid4()),
            "answers": [],
        }
        r = client.post(
            f"{API}/{exam['id']}/submit",
            headers=normal_user_token_headers,
            json=submit_body,
        )
        assert r.status_code == 403


# ─── Attempts ─────────────────────────────────────────────────────────────────

class TestAttempts:

    def test_get_attempts_empty(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None

        exam, _ = _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id)
        )

        r = client.get(f"{API}/{exam['id']}/attempts", headers=normal_user_token_headers)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_get_attempts_after_submission(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None
        user_id = str(test_user.id)

        exam, questions = _create_published_exam_for_user(
            client, superuser_token_headers, user_id
        )

        # Start and submit
        r = client.post(f"{API}/{exam['id']}/start", headers=normal_user_token_headers)
        attempt_id = r.json()["attempt_id"]

        answers = []
        for q in questions:
            correct_ids = [o["id"] for o in q["options"] if o.get("is_correct")]
            answers.append({"question_id": q["id"], "selected_option_ids": correct_ids})

        client.post(
            f"{API}/{exam['id']}/submit",
            headers=normal_user_token_headers,
            json={"attempt_id": attempt_id, "answers": answers},
        )

        # Get attempts
        r = client.get(f"{API}/{exam['id']}/attempts", headers=normal_user_token_headers)
        assert r.status_code == 200, r.text
        attempts = r.json()
        assert len(attempts) >= 1
        assert attempts[0]["status"] == "SUBMITTED"

    def test_get_attempts_not_enrolled(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
    ) -> None:
        payload = _exam_payload()
        r = client.post(ADMIN_API, headers=superuser_token_headers, json=payload)
        exam = r.json()

        r = client.get(f"{API}/{exam['id']}/attempts", headers=normal_user_token_headers)
        assert r.status_code == 403


# ─── Attempt Answers ──────────────────────────────────────────────────────────

class TestAttemptAnswers:

    def test_get_attempt_answers(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None
        user_id = str(test_user.id)

        exam, questions = _create_published_exam_for_user(
            client, superuser_token_headers, user_id
        )

        # Start and submit
        r = client.post(f"{API}/{exam['id']}/start", headers=normal_user_token_headers)
        attempt_id = r.json()["attempt_id"]

        answers = []
        for q in questions:
            correct_ids = [o["id"] for o in q["options"] if o.get("is_correct")]
            answers.append({"question_id": q["id"], "selected_option_ids": correct_ids})

        client.post(
            f"{API}/{exam['id']}/submit",
            headers=normal_user_token_headers,
            json={"attempt_id": attempt_id, "answers": answers},
        )

        # Get attempt answers
        r = client.get(
            f"{API}/{exam['id']}/attempts/{attempt_id}/answers",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["attempt_id"] == attempt_id
        assert data["exam_name"] == exam["name"]
        assert data["total_score"] == 100.0
        assert data["passed"] is True
        assert "answers" in data
        assert len(data["answers"]) == 2

        # Verify correct_option_ids are included (show_answer is True)
        for ans in data["answers"]:
            assert "correct_option_ids" in ans
            assert "is_correct" in ans
            assert "score_awarded" in ans

    def test_get_attempt_answers_not_enrolled(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None

        # Create exam for the test user (enrolled)
        exam, questions = _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id)
        )

        # Start and submit with normal user
        r = client.post(f"{API}/{exam['id']}/start", headers=normal_user_token_headers)
        attempt_id = r.json()["attempt_id"]

        answers = []
        for q in questions:
            correct_ids = [o["id"] for o in q["options"] if o.get("is_correct")]
            answers.append({"question_id": q["id"], "selected_option_ids": correct_ids})

        client.post(
            f"{API}/{exam['id']}/submit",
            headers=normal_user_token_headers,
            json={"attempt_id": attempt_id, "answers": answers},
        )

        # This user is enrolled, so it should work. But let's test with a different exam
        # that the user is NOT enrolled in
        payload = _exam_payload()
        r = client.post(ADMIN_API, headers=superuser_token_headers, json=payload)
        other_exam = r.json()

        fake_attempt_id = str(uuid.uuid4())
        r = client.get(
            f"{API}/{other_exam['id']}/attempts/{fake_attempt_id}/answers",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 403

    def test_get_attempt_answers_attempt_not_found(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None

        exam, _ = _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id)
        )

        fake_attempt_id = str(uuid.uuid4())
        r = client.get(
            f"{API}/{exam['id']}/attempts/{fake_attempt_id}/answers",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 404


# ─── My Pending Exams ─────────────────────────────────────────────────────────

PENDING_API = f"{settings.API_V1_STR}/exams/my-pending"


class TestMyPendingExams:

    def test_my_pending_exams_empty(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Pending exams endpoint returns valid structure."""
        r = client.get(PENDING_API, headers=normal_user_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "data" in data
        assert "count" in data
        assert isinstance(data["data"], list)
        assert isinstance(data["count"], int)
        assert data["count"] == len(data["data"])

    def test_my_pending_exams_shows_published_not_completed(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Pending exams include published exams where user is enrolled and not completed."""
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None

        _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id)
        )

        r = client.get(PENDING_API, headers=normal_user_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["count"] >= 1
        assert len(data["data"]) >= 1
        # Verify fields
        exam = data["data"][0]
        assert "id" in exam
        assert "name" in exam
        assert "start_at" in exam
        assert "end_at" in exam
        assert "is_in_progress" in exam

    def test_my_pending_exams_excludes_completed(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Completed exams should not appear in pending list."""
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None
        user_id = str(test_user.id)

        exam, questions = _create_published_exam_for_user(
            client, superuser_token_headers, user_id
        )

        # Start and submit all correct to complete the exam
        r = client.post(f"{API}/{exam['id']}/start", headers=normal_user_token_headers)
        attempt_id = r.json()["attempt_id"]

        answers = []
        for q in questions:
            correct_ids = [o["id"] for o in q["options"] if o.get("is_correct")]
            answers.append({"question_id": q["id"], "selected_option_ids": correct_ids})

        client.post(
            f"{API}/{exam['id']}/submit",
            headers=normal_user_token_headers,
            json={"attempt_id": attempt_id, "answers": answers},
        )

        # Now the exam should NOT be in pending
        r = client.get(PENDING_API, headers=normal_user_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        pending_ids = [e["id"] for e in data["data"]]
        assert exam["id"] not in pending_ids

    def test_my_pending_exams_excludes_ended(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Exams that have already ended should not appear in pending list."""
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None

        # Create an exam that ended in the past
        ended_exam, _ = _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id),
            name="Ended Exam For Pending Test",
            start_at=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            end_at=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        )

        r = client.get(PENDING_API, headers=normal_user_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        # The ended exam should NOT be in the pending list
        pending_ids = [e["id"] for e in data["data"]]
        assert ended_exam["id"] not in pending_ids

    def test_my_pending_exams_sorts_in_progress_first(
        self, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """In-progress exams should be sorted before upcoming exams."""
        test_user = get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
        assert test_user is not None

        # Create an upcoming exam (starts tomorrow)
        upcoming_exam, _ = _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id),
            name="Upcoming Exam For Sort Test",
            start_at=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            end_at=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        )

        # Create an in-progress exam (started 1 hour ago)
        active_exam, _ = _create_published_exam_for_user(
            client, superuser_token_headers, str(test_user.id),
            name="Active Exam For Sort Test",
            start_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            end_at=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        )

        r = client.get(PENDING_API, headers=normal_user_token_headers)
        assert r.status_code == 200, r.text
        data = r.json()

        # Find our exams in the results
        pending_ids = [e["id"] for e in data["data"]]
        assert upcoming_exam["id"] in pending_ids
        assert active_exam["id"] in pending_ids

        # Active exam should come before upcoming exam in the sorted list
        active_idx = pending_ids.index(active_exam["id"])
        upcoming_idx = pending_ids.index(upcoming_exam["id"])
        assert active_idx < upcoming_idx

        # Verify is_in_progress flags
        active_entry = next(e for e in data["data"] if e["id"] == active_exam["id"])
        upcoming_entry = next(e for e in data["data"] if e["id"] == upcoming_exam["id"])
        assert active_entry["is_in_progress"] is True
        assert upcoming_entry["is_in_progress"] is False

    def test_my_pending_exams_no_auth(self, client: TestClient) -> None:
        """Pending endpoint requires auth."""
        r = client.get(PENDING_API)
        assert r.status_code == 401


# ─── Auth Tests ───────────────────────────────────────────────────────────────

class TestAuth:

    def test_no_auth_returns_401(self, client: TestClient) -> None:
        """All user endpoints require authentication."""
        r = client.get(API)
        assert r.status_code == 401

    def test_user_endpoints_accessible_with_normal_user(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Normal authenticated users can access user endpoints (no admin role required)."""
        r = client.get(API, headers=normal_user_token_headers)
        assert r.status_code == 200
