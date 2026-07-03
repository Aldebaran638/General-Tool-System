"""
Question Bank Management Module — self-registration
"""

from app.modules.question_bank_management.models import (
    QuestionBankOption,
    QuestionBankQuestion,
    QuestionBankSet,
)
from app.modules.question_bank_management.router import router
from app.modules.registry import registry

registry.register(
    name="question_bank_management",
    group="exam",
    router=router,
    models=[QuestionBankSet, QuestionBankQuestion, QuestionBankOption],
)
