"""
Reimbursement Exports Constants

Defines business constants for the reimbursement_exports tool module.
"""

# =============================================================================
# Category Order
# =============================================================================

CATEGORY_TRANSPORTATION = "transportation"
CATEGORY_MEALS_ENTERTAINMENT = "meals_entertainment"
CATEGORY_VEHICLE = "vehicle"
CATEGORY_OTHER_PROJECT = "other_project"

CATEGORY_ORDER = [
    CATEGORY_TRANSPORTATION,
    CATEGORY_MEALS_ENTERTAINMENT,
    CATEGORY_VEHICLE,
    CATEGORY_OTHER_PROJECT,
]

# =============================================================================
# Export Status Constants
# =============================================================================

STATUS_GENERATED = "generated"
STATUS_PURGED = "purged"

VALID_STATUSES = [
    STATUS_GENERATED,
    STATUS_PURGED,
]

# =============================================================================
# Retention Constants
# =============================================================================

DEFAULT_RETENTION_DAYS = 1
MIN_RETENTION_DAYS = 1
MAX_RETENTION_DAYS = 365

# =============================================================================
# Settings Keys
# =============================================================================

SETTING_RETENTION_DAYS = "reimbursement_export_retention_days"

# =============================================================================
# File Storage
# =============================================================================

EXPORT_DIR = "runtime_data/exports/finance/reimbursement"
EXCEL_TEMPLATE_PATH = "docs/報銷表模板最新.xlsx"

# =============================================================================
# Sheet Names
# =============================================================================

SHEET_DETAIL = "報銷單"
SHEET_CATEGORY = "報銷單分类"
