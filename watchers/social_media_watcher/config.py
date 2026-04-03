"""
Social Media Configuration

Configuration for social media management including:
- Rate limits (10 posts/day per platform)
- High engagement threshold (3x average)
- Platform-specific settings
"""

from typing import Dict, List
from enum import Enum

class PostStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class SocialMediaConfig:
    # Rate limiting
    MAX_POSTS_PER_DAY = 10
    MAX_POSTS_PER_PLATFORM_PER_DAY = 10
    
    # Engagement thresholds
    HIGH_ENGAGEMENT_MULTIPLIER = 3.0
    LOW_ENGAGEMENT_MULTIPLIER = 0.5
    
    # Polling configuration
    POLL_INTERVAL_SECONDS = 300
    ENGAGEMENT_CHECK_INTERVAL_SECONDS = 300
    
    # Content validation
    MAX_CONTENT_LENGTH = 280
    MAX_MEDIA_URLS = 4
    
    # Platforms
    SUPPORTED_PLATFORMS = ["facebook", "instagram", "twitter"]
    
    # Platform-specific limits
    PLATFORM_LIMITS = {
        "facebook": {"max_length": 63206, "max_media": 10},
        "instagram": {"max_length": 2200, "max_media": 10},
        "twitter": {"max_length": 280, "max_media": 4}
    }
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 300
    
    # Circuit breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = 0.20
    
    @classmethod
    def validate_content_length(cls, content: str) -> bool:
        return len(content) <= cls.MAX_CONTENT_LENGTH
    
    @classmethod
    def validate_platforms(cls, platforms: List[str]) -> bool:
        if not platforms:
            return False
        return all(p in cls.SUPPORTED_PLATFORMS for p in platforms)
    
    @classmethod
    def validate_media_urls(cls, media_urls: List[str]) -> bool:
        return len(media_urls) <= cls.MAX_MEDIA_URLS
