"""
Exam Management Module — self-registration
"""

from app.modules.exam_management.models import (
    Exam,
    ExamParticipant,
    Question,
    QuestionOption,
)
from app.modules.exam_management.router import router
from app.modules.registry import registry

registry.register(
    name="exam_management",
    group="exam",
    router=router,
    models=[Exam, Question, QuestionOption, ExamParticipant],
)
