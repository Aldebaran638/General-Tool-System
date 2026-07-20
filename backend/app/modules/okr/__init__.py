"""
OKR Module — self-registration
"""

from app.modules.okr.models import Department, KeyResult, Objective
from app.modules.okr.router import router
from app.modules.registry import registry

registry.register(
    name="okr",
    group="okr",
    router=router,
    models=[Department, Objective, KeyResult],
)
