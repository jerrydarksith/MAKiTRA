from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


class UserStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"


class AccessRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ContactRegistrationResult(str, Enum):
    FIRST_SUPER_ADMIN_CREATED = "first_super_admin_created"
    ACCESS_REQUEST_CREATED = "access_request_created"
    ACCESS_REQUEST_ALREADY_PENDING = "access_request_already_pending"
    USER_ALREADY_REGISTERED = "user_already_registered"


class AccessRequestReviewResult(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    ALREADY_PROCESSED = "already_processed"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"
