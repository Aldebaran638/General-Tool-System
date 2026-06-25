"""
AI Assistant Module — self-registration
"""

from app.modules.ai_assistant.models import AIAssistantThread
from app.modules.ai_assistant.router import router
from app.modules.registry import registry

registry.register(
    name="ai_assistant",
    group="exam",
    router=router,
    models=[AIAssistantThread],
)
