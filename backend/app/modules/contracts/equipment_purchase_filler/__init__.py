"""
Equipment Purchase Contract Filler Tool Module

Provides a dedicated tool for filling the equipment purchase contract template
(设备购销合同) with named versions and DOCX export.
"""

from app.modules.registry import register_module

from .models import EquipmentPurchaseFilledVersion
from .router import router

register_module(
    name="equipment_purchase_filler",
    group="contracts",
    router=router,
    models=[EquipmentPurchaseFilledVersion],
)

__all__ = ["router"]
