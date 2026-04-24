"""
Purchase Records Constants

Defines business constants for the purchase_records tool module.
"""

# =============================================================================
# Status Constants
# =============================================================================

STATUS_DRAFT = "draft"
STATUS_SUBMITTED = "submitted"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"

VALID_STATUSES = [
    STATUS_DRAFT,
    STATUS_SUBMITTED,
    STATUS_APPROVED,
    STATUS_REJECTED,
]

# =============================================================================
# Invoice Match Status Constants
# =============================================================================

INVOICE_UNMATCHED = "unmatched"
INVOICE_MATCHED = "matched"

VALID_INVOICE_MATCH_STATUSES = [
    INVOICE_UNMATCHED,
    INVOICE_MATCHED,
]

# =============================================================================
# Currency Constants (ISO 4217)
# =============================================================================

VALID_CURRENCIES = [
    "CNY",
    "USD",
    "EUR",
    "JPY",
    "HKD",
    "GBP",
    "AUD",
    "CAD",
    "SGD",
]

# =============================================================================
# Category Constants
# =============================================================================

CATEGORY_TRANSPORTATION = "transportation"
CATEGORY_MEALS_ENTERTAINMENT = "meals_entertainment"
CATEGORY_VEHICLE = "vehicle"
CATEGORY_OTHER_PROJECT = "other_project"

VALID_CATEGORIES = [
    CATEGORY_TRANSPORTATION,
    CATEGORY_MEALS_ENTERTAINMENT,
    CATEGORY_VEHICLE,
    CATEGORY_OTHER_PROJECT,
]

# =============================================================================
# Subcategory Constants
# =============================================================================

SUBCATEGORY_AGV = "agv"
SUBCATEGORY_PAINTING_ROBOT = "painting_robot"
SUBCATEGORY_REBAR_ROBOT = "rebar_robot"
SUBCATEGORY_FLEET_SCHEDULING = "fleet_scheduling"
SUBCATEGORY_RD_EXPENSE = "rd_expense"

VALID_SUBCATEGORIES = [
    SUBCATEGORY_AGV,
    SUBCATEGORY_PAINTING_ROBOT,
    SUBCATEGORY_REBAR_ROBOT,
    SUBCATEGORY_FLEET_SCHEDULING,
    SUBCATEGORY_RD_EXPENSE,
]
