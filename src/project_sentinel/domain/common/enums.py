from enum import StrEnum


class Status(StrEnum):
    INBOX = "inbox"
    PLANNED = "planned"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class Priority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SOMEDAY = "someday"


class Source(StrEnum):
    MANUAL = "manual"
    GITHUB = "github"
    TICKTICK = "ticktick"
    GOOGLE = "google"
    EMAIL = "email"
    CALENDAR = "calendar"
    WAZUH = "wazuh"
    AI = "ai"
