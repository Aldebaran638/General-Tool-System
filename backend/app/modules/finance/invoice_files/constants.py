"""
Invoice Files Constants

Defines business constants for the invoice_files tool module.
"""

# =============================================================================
# Status Constants
# =============================================================================

STATUS_DRAFT = "draft"
STATUS_CONFIRMED = "confirmed"
STATUS_VOIDED = "voided"

VALID_STATUSES = [
    STATUS_DRAFT,
    STATUS_CONFIRMED,
    STATUS_VOIDED,
]

# =============================================================================
# Invoice Type Constants
# =============================================================================

INVOICE_TYPE_GENERAL = "general_invoice"
INVOICE_TYPE_VAT_SPECIAL = "vat_special_invoice"
INVOICE_TYPE_TOLL = "toll_invoice"
INVOICE_TYPE_OTHER = "other"

VALID_INVOICE_TYPES = [
    INVOICE_TYPE_GENERAL,
    INVOICE_TYPE_VAT_SPECIAL,
    INVOICE_TYPE_TOLL,
    INVOICE_TYPE_OTHER,
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
