"""
Exceptions — WhatsApp Skills Exceptions
=========================================
Custom exceptions for the WhatsApp skills framework.

Usage:
    from skills.whatsapp.exceptions import (
        WhatsAppError,
        ChatWindowClosedError,
        InvalidPhoneError,
        TemplateValidationError,
        APIError,
    )
"""


class WhatsAppError(Exception):
    """Base exception for all WhatsApp skills errors."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# ==============================================================================
# CONFIGURATION ERRORS
# ==============================================================================

class ConfigError(WhatsAppError):
    """Raised when required configuration is missing or invalid."""
    pass


class MissingAPIKeyError(ConfigError):
    """Raised when DOUBLETICK_API_KEY is not set."""
    pass


# ==============================================================================
# PHONE NUMBER ERRORS
# ==============================================================================

class InvalidPhoneError(WhatsAppError):
    """Raised when a phone number cannot be parsed to valid Indian format."""
    def __init__(self, phone: str, reason: str = None):
        self.phone = phone
        self.reason = reason or "Could not parse to 91XXXXXXXXXX format"
        super().__init__(f"Invalid phone '{phone}': {self.reason}")
        self.details = {"phone": phone, "reason": self.reason}


class PhoneFormatError(InvalidPhoneError):
    """Raised when phone has wrong format."""
    pass


# ==============================================================================
# CHAT WINDOW ERRORS
# ==============================================================================

class ChatWindowClosedError(WhatsAppError):
    """
    Raised when trying to send free-form text to a customer whose
    24-hour chat window has closed.

    This is a NORMAL business logic error — not a system failure.
    Catch this to decide: template message or ask customer to reply first.
    """
    def __init__(self, phone: str, last_reply_at: str = None):
        self.phone = phone
        self.last_reply_at = last_reply_at
        message = (
            f"Chat window closed for {phone}. "
            f"Customer must reply first, or use a template message."
        )
        super().__init__(message)
        self.details = {
            "phone": phone,
            "last_reply_at": last_reply_at,
            "recommendation": "Use send_template_message() instead, or ask customer to reply",
        }


# ==============================================================================
# TEMPLATE ERRORS
# ==============================================================================

class TemplateValidationError(WhatsAppError):
    """
    Raised when template variables are missing, wrong count, or invalid.
    Each template has specific placeholder requirements.
    """
    def __init__(self, template_name: str, expected_count: int, actual_count: int = None):
        self.template_name = template_name
        self.expected_count = expected_count
        self.actual_count = actual_count

        message = (
            f"Template '{template_name}' requires {expected_count} placeholder(s). "
        )
        if actual_count is not None:
            message += f"Got {actual_count}."
        else:
            message += "None provided."

        super().__init__(message)
        self.details = {
            "template_name": template_name,
            "expected_count": expected_count,
            "actual_count": actual_count,
        }


class MediaValidationError(WhatsAppError):
    """Raised when media URL is invalid or media is missing for a template that requires it."""
    def __init__(self, template_name: str, media_type: str, reason: str = None):
        self.template_name = template_name
        self.media_type = media_type
        self.reason = reason or "Media URL is required for this template"
        super().__init__(f"Media validation failed for '{template_name}': {self.reason}")
        self.details = {
            "template_name": template_name,
            "media_type": media_type,
            "reason": self.reason,
        }


# ==============================================================================
# API ERRORS
# ==============================================================================

class APIError(WhatsAppError):
    """Raised when DoubleTick API returns an error."""
    def __init__(self, status_code: int, message: str, response_body: dict = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"DoubleTick API error ({status_code}): {message}")
        self.details = {
            "status_code": status_code,
            "message": message,
            "response_body": response_body,
        }


class APITimeoutError(APIError):
    """Raised when DoubleTick API call times out."""
    def __init__(self, timeout_seconds: int):
        super().__init__(
            status_code=None,
            message=f"Request timed out after {timeout_seconds}s",
        )
        self.details = {"timeout_seconds": timeout_seconds}


class ChatWindowAPIError(WhatsAppError):
    """Raised when chat window status check fails."""
    def __init__(self, phone: str, reason: str):
        self.phone = phone
        self.reason = reason
        super().__init__(f"Chat window check failed for {phone}: {reason}")
        self.details = {"phone": phone, "reason": reason}


# ==============================================================================
# WORKFLOW ERRORS
# ==============================================================================

class CustomerNotFoundError(WhatsAppError):
    """Raised when customer cannot be found in contacts."""
    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"Customer not found: {identifier}")
        self.details = {"identifier": identifier}


class WorkflowError(WhatsAppError):
    """Raised when a business workflow fails."""
    pass


class CRMError(WhatsAppError):
    """Raised when CRM operations fail."""
    pass


# ==============================================================================
# ERROR FACTORY
# ==============================================================================

def raise_from_response(response: dict, status_code: int) -> None:
    """
    Convert an API error response to the appropriate exception.
    Call this when DoubleTick returns a non-2xx response.
    """
    error_message = (
        response.get("message") or
        response.get("error") or
        response.get("errorMessage") or
        str(response)
    )
    raise APIError(status_code, error_message, response)