"""
Standardized application exceptions and error handling utilities.
"""

from typing import Any, Optional


class OmnixException(Exception):
    """Base exception for all domain and operational errors in OMNIX."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class NotFoundException(OmnixException):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details=details,
        )


class BusinessRuleViolationException(OmnixException):
    """Raised when an operation violates procurement, budget, or inventory rules."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="BUSINESS_RULE_VIOLATION",
            details=details,
        )


class ExternalServiceException(OmnixException):
    """Raised when an external dependency (Groq, vector DB, ML runner) fails."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
        )
