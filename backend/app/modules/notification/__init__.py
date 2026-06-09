"""
Notification Module — self-registration
"""

from app.modules.notification.models import Notification
from app.modules.notification.router import router
from app.modules.registry import registry

registry.register(
    name="notification",
    group="exam",
    router=router,
    models=[Notification],
)
