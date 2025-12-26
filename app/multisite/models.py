"""
Data Models - MULTI-05

Data structures for site groups, activity logging, permissions, and quotas.
"""

from enum import Enum
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Any, Optional


# ============================================================================
# ENUMS
# ============================================================================

class EventType(Enum):
    """Activity event types."""
    SITE_CREATED = "site.created"
    SITE_DELETED = "site.deleted"
    SITE_ENABLED = "site.enabled"
    SITE_DISABLED = "site.disabled"
    SITE_UPDATED = "site.updated"

    DOMAIN_ADDED = "domain.added"
    DOMAIN_REMOVED = "domain.removed"

    CONFIG_SAVED = "config.saved"
    CONFIG_RESTORED = "config.restored"

    USER_ADDED = "user.added"
    USER_REMOVED = "user.removed"
    PERMISSION_CHANGED = "permission.changed"

    BACKUP_CREATED = "backup.created"
    BACKUP_RESTORED = "backup.restored"

    QUOTA_EXCEEDED = "quota.exceeded"
    QUOTA_UPDATED = "quota.updated"

    GROUP_CREATED = "group.created"
    GROUP_DELETED = "group.deleted"


class UserRole(Enum):
    """Predefined user roles."""
    ADMIN = "admin"           # Full access
    EDITOR = "editor"         # Can edit content
    VIEWER = "viewer"         # Read-only access
    OWNER = "owner"           # Site owner (can delete)
    DEVELOPER = "developer"   # Can manage settings


class ResourceType(Enum):
    """Types of resources for quotas."""
    STORAGE = "storage"       # Bytes
    BANDWIDTH = "bandwidth"   # Bytes
    API_CALLS = "api_calls"   # Count
    USERS = "users"           # Count
    PAGES = "pages"           # Count


# ============================================================================
# SITE GROUPS
# ============================================================================

@dataclass
class SiteGroup:
    """Represents a site group."""
    id: str
    name: str
    description: str = ""
    parent_id: Optional[str] = None
    sites: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return asdict(self)


# ============================================================================
# ACTIVITY LOGGING
# ============================================================================

@dataclass
class ActivityEvent:
    """Represents an activity event."""
    event_type: EventType
    site_id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    resource_id: Optional[str] = None
    status: str = "success"  # success, failure, warning

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActivityEvent':
        """Create from dict."""
        data['event_type'] = EventType(data['event_type'])
        return cls(**data)


# ============================================================================
# PERMISSIONS
# ============================================================================

@dataclass
class Permission:
    """Represents a single permission."""
    name: str
    description: str = ""
    category: str = ""  # admin, content, settings, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return asdict(self)


@dataclass
class Role:
    """Represents a user role."""
    name: str
    description: str = ""
    permissions: List[str] = field(default_factory=list)
    is_custom: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return asdict(self)


@dataclass
class SiteUser:
    """Represents a user with access to a site."""
    user_id: str
    username: str
    email: str
    role: UserRole
    permissions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        data = asdict(self)
        data['role'] = self.role.value
        return data


# ============================================================================
# QUOTAS & LIMITS
# ============================================================================

@dataclass
class QuotaLimit:
    """Represents a quota limit."""
    resource: ResourceType
    limit: int  # Bytes for storage/bandwidth, count for others
    warning_threshold: int = None  # Alert at % of limit
    soft_limit: bool = False  # Allows exceeding temporarily

    def __post_init__(self):
        """Set default warning threshold."""
        if self.warning_threshold is None:
            self.warning_threshold = int(self.limit * 0.8)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            'resource': self.resource.value,
            'limit': self.limit,
            'warning_threshold': self.warning_threshold,
            'soft_limit': self.soft_limit
        }


@dataclass
class QuotaUsage:
    """Tracks quota usage for a site."""
    site_id: str
    resource: ResourceType
    used: int
    limit: int
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    alerts_sent: List[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        """Get usage percentage."""
        if self.limit == 0:
            return 0
        return (self.used / self.limit) * 100

    @property
    def remaining(self) -> int:
        """Get remaining quota."""
        return max(0, self.limit - self.used)

    @property
    def is_exceeded(self) -> bool:
        """Check if quota exceeded."""
        return self.used > self.limit

    @property
    def is_warning(self) -> bool:
        """Check if at warning threshold."""
        warning_threshold = int(self.limit * 0.8)
        return self.used >= warning_threshold

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            'site_id': self.site_id,
            'resource': self.resource.value,
            'used': self.used,
            'limit': self.limit,
            'percentage': self.percentage,
            'remaining': self.remaining,
            'is_exceeded': self.is_exceeded,
            'is_warning': self.is_warning,
            'last_updated': self.last_updated,
            'alerts_sent': self.alerts_sent
        }


# ============================================================================
# REPORTS
# ============================================================================

@dataclass
class SiteReport:
    """Comprehensive report for a site."""
    site_id: str
    site_name: str

    # Activity
    total_events: int = 0
    recent_events: List[ActivityEvent] = field(default_factory=list)

    # Users
    user_count: int = 0
    users: List[SiteUser] = field(default_factory=list)

    # Quotas
    quotas: List[QuotaUsage] = field(default_factory=list)

    # Metadata
    created_at: str = ""
    last_activity: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            'site_id': self.site_id,
            'site_name': self.site_name,
            'total_events': self.total_events,
            'recent_events': [e.to_dict() for e in self.recent_events],
            'user_count': self.user_count,
            'users': [u.to_dict() for u in self.users],
            'quotas': [q.to_dict() for q in self.quotas],
            'created_at': self.created_at,
            'last_activity': self.last_activity
        }
