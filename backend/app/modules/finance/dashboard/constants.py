"""Finance Dashboard Constants

Defines constants for the finance dashboard tool module.
"""

# =============================================================================
# Pending List Limits
# =============================================================================

PENDING_DEFAULT_LIMIT = 20
PENDING_MAX_LIMIT = 100


# =============================================================================
# Pending Item Type Constants
# =============================================================================

PENDING_TYPE_PURCHASE_UNMATCHED = "purchase_record_unmatched"
PENDING_TYPE_INVOICE_UNALLOCATED = "invoice_file_unallocated"
PENDING_TYPE_MATCH_NEEDS_REVIEW = "match_needs_review"


# =============================================================================
# Severity Constants
# =============================================================================

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_DANGER = "danger"


# =============================================================================
# Pending Item Priority
# =============================================================================
# Higher number → higher priority. Used to rank pending items when truncating
# the result list down to `limit`. needs_review beats unallocated invoices,
# which beats unmatched purchases — fixing a broken match is the most urgent.

PRIORITY_BY_TYPE: dict[str, int] = {
    PENDING_TYPE_MATCH_NEEDS_REVIEW: 30,
    PENDING_TYPE_INVOICE_UNALLOCATED: 20,
    PENDING_TYPE_PURCHASE_UNMATCHED: 10,
}

SEVERITY_BY_TYPE: dict[str, str] = {
    PENDING_TYPE_MATCH_NEEDS_REVIEW: SEVERITY_WARNING,
    PENDING_TYPE_INVOICE_UNALLOCATED: SEVERITY_INFO,
    PENDING_TYPE_PURCHASE_UNMATCHED: SEVERITY_INFO,
}


# =============================================================================
# Scope Labels
# =============================================================================

SCOPE_SELF = "self"
SCOPE_GLOBAL = "global"
