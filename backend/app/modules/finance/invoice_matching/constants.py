"""
Invoice Matching Constants

Defines business constants for the invoice_matching tool module.
"""

# =============================================================================
# Match Status Constants
# =============================================================================

MATCH_STATUS_CONFIRMED = "confirmed"
MATCH_STATUS_CANCELLED = "cancelled"
MATCH_STATUS_NEEDS_REVIEW = "needs_review"
MATCH_STATUS_APPROVED = "approved"

VALID_MATCH_STATUSES = [
    MATCH_STATUS_CONFIRMED,
    MATCH_STATUS_CANCELLED,
    MATCH_STATUS_NEEDS_REVIEW,
    MATCH_STATUS_APPROVED,
]

# =============================================================================
# Candidate Thresholds
# =============================================================================

SCORE_THRESHOLD_STRONG = 80
SCORE_THRESHOLD_WEAK = 60

# =============================================================================
# Match Rules
# =============================================================================

MAX_DATE_DIFF_DAYS = 7
AMOUNT_TOLERANCE = 0.01

# =============================================================================
# Score Breakdown Constants
# =============================================================================

SCORE_AMOUNT_MATCH = 50
SCORE_CURRENCY_MATCH = 10
SCORE_DATE_EXACT = 20
SCORE_DATE_NEAR = 10
SCORE_DATE_FAR = 5
SCORE_TEXT_SIMILARITY = 15
SCORE_KEYWORD_MATCH = 5
