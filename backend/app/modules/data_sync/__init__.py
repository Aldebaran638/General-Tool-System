"""
Data Sync Module — self-registration
"""

from app.modules.data_sync.models import SyncTask, WecomDepartment
from app.modules.data_sync.router import router
from app.modules.registry import registry

registry.register(
    name="data_sync",
    group="data_sync",
    router=router,
    models=[WecomDepartment, SyncTask],
)
