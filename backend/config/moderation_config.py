class ModerationConfig:
    """Configuration for auto-moderation system"""
    
    # Score thresholds
    AUTO_APPROVE_THRESHOLD = 80  # Score >= 80: Auto-approve
    MANUAL_REVIEW_THRESHOLD = 50  # Score 50-79: Manual review
    # Score < 50: Auto-reject
    
    # Image requirements
    MIN_IMAGES_REQUIRED = 0  # Minimum (0 = optional but penalized)
    RECOMMENDED_IMAGES = 3   # Recommended minimum
    MAX_IMAGES_ALLOWED = 20
    
    # Video requirements
    MAX_VIDEOS_ALLOWED = 5
    VIDEO_BONUS_POINTS = 10
    
    # Description requirements
    MIN_DESCRIPTION_LENGTH = 50
    RECOMMENDED_DESCRIPTION_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 2000
    
    # Price limits (KES)
    MIN_REASONABLE_PRICE = 5000
    MAX_REASONABLE_PRICE = 1000000
    SUSPICIOUS_LOW_PRICE = 1000
    
    # Penalties (point deductions)
    PENALTY_NO_IMAGES = 40
    PENALTY_FEW_IMAGES = 20
    PENALTY_SHORT_DESCRIPTION = 25
    PENALTY_INVALID_PRICE = 30
    PENALTY_SPAM_KEYWORD = 15
    PENALTY_MISSING_FIELD = 8
    
    # Bonuses (point additions)
    BONUS_MANY_IMAGES = 5
    BONUS_HAS_VIDEO = 10
    BONUS_DETAILED_DESCRIPTION = 5
    BONUS_HAS_COORDINATES = 5
    
    # Auto-moderation enabled
    AUTO_MODERATION_ENABLED = True
    
    # Notification settings
    NOTIFY_LANDLORD_ON_APPROVAL = True
    NOTIFY_LANDLORD_ON_REJECTION = True
    NOTIFY_ADMIN_ON_FLAGGED = True
