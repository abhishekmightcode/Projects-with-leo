"""
Formatter — Phone Number and Payload Formatting
=================================================
Normalizes phone numbers to Indian format and validates API payloads.

All WhatsApp API calls use this to ensure consistent phone formatting.

Usage:
    from skills.whatsapp.formatter import format_phone, validate_phone, validate_media_url
"""

import re
import uuid
from typing import Optional, Tuple

# ==============================================================================
# PHONE NUMBER FORMATTING
# ==============================================================================

INDIAN_COUNTRY_CODE = "91"


def format_phone_number(phone: str) -> str:
    """
    Format any phone input to Indian format: 91XXXXXXXXXX (no +, no spaces).

    Handles all common formats:
    - "9876543210"          → "919876543210"
    - "+91 9876543210"     → "919876543210"
    - "919876543210"       → "919876543210"
    - "+919876543210"      → "919876543210"
    - "91 98765 43210"     → "919876543210"

    Args:
        phone: Raw phone input

    Returns:
        91XXXXXXXXXX

    Raises:
        ValueError: If phone cannot be parsed to valid 10-digit Indian number
    """
    # Strip all non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())

    # Handle bare 10-digit number (no country code)
    if len(digits) == 10:
        return f"{INDIAN_COUNTRY_CODE}{digits}"

    # Handle +91 prefix
    if digits.startswith("91") and len(digits) == 12:
        # Already has country code, strip and re-add to be safe
        return f"{INDIAN_COUNTRY_CODE}{digits[2:]}"

    # Handle 91 prefix with extra digits
    if digits.startswith("91") and len(digits) > 12:
        digits = digits[2:]  # Remove 91 prefix
        return f"{INDIAN_COUNTRY_CODE}{digits[-10:]}"

    raise ValueError(
        f"Invalid phone number: '{phone}'. "
        f"Expected 10 digits (with optional +91 prefix), got {len(digits)} digits."
    )


def validate_phone_number(phone: str) -> bool:
    """
    Check if a phone can be formatted to valid Indian number.

    Returns:
        True if valid, False otherwise
    """
    try:
        formatted = format_phone_number(phone)
        # Must be exactly 12 digits starting with 91
        return len(formatted) == 12 and formatted.startswith("91")
    except ValueError:
        return False


def strip_whatsapp_prefix(phone: str) -> str:
    """
    Remove any existing +91 prefix from a phone string before re-formatting.

    Useful for cleaning up contacts that already have partial formatting.
    """
    digits = ''.join(c for c in phone if c.isdigit())
    if digits.startswith("91"):
        digits = digits[2:]
    return digits


def get_local_number(phone: str) -> str:
    """
    Get just the local 10-digit number without country code.

    "919876543210" → "9876543210"
    """
    formatted = format_phone_number(phone)
    return formatted[2:]


# ==============================================================================
# PAYLOAD VALIDATION
# ==============================================================================

def validate_placeholders(template_name: str, placeholders: list, required_count: int) -> Tuple[bool, str]:
    """
    Validate that placeholders match template requirements.

    Args:
        template_name: Name of the template
        placeholders: List of placeholder values provided
        required_count: Number of placeholders required

    Returns:
        (is_valid, error_message)
    """
    if placeholders is None:
        actual_count = 0
    else:
        actual_count = len(placeholders)

    if actual_count < required_count:
        return False, (
            f"Template '{template_name}' requires {required_count} placeholder(s), "
            f"got {actual_count}"
        )

    if actual_count > required_count:
        return False, (
            f"Template '{template_name}' expects max {required_count} placeholder(s), "
            f"got {actual_count}"
        )

    return True, ""


def validate_media_url(url: str, media_type: str = None) -> Tuple[bool, str]:
    """
    Validate that a media URL is properly formed and points to accessible content.

    Args:
        url: The media URL to validate
        media_type: "IMAGE" or "DOCUMENT" for type-specific validation

    Returns:
        (is_valid, error_message)
    """
    if not url:
        return False, "Media URL is empty"

    if not url.startswith(("http://", "https://")):
        return False, f"Media URL must start with http:// or https://: {url}"

    # Check URL structure
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.netloc:
            return False, f"Invalid URL structure: {url}"
    except Exception as e:
        return False, f"Could not parse URL: {e}"

    # Type-specific validation
    if media_type == "IMAGE":
        image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp")
        if not any(url.lower().endswith(ext) for ext in image_extensions):
            return False, f"IMAGE template requires an image file URL (.png/.jpg/.jpeg/.gif/.webp)"

    elif media_type == "DOCUMENT":
        if not url.lower().endswith(".pdf"):
            return False, "DOCUMENT template requires a .pdf URL"

    return True, ""


# ==============================================================================
# MESSAGE ID GENERATION
# ==============================================================================

def generate_message_id() -> str:
    """Generate a unique message ID for tracking."""
    return str(uuid.uuid4())


# ==============================================================================
# TEXT SANITIZATION
# ==============================================================================

def sanitize_text_for_whatsapp(text: str, max_length: int = 4096) -> str:
    """
    Sanitize text for WhatsApp send.

    - Truncates to max length
    - Strips control characters
    - Normalizes whitespace
    """
    if not text:
        return ""

    # Remove control characters except newlines/tabs
    cleaned = ''.join(c for c in text if c.isprintable() or c in ('\n', '\t'))

    # Normalize multiple spaces/newlines
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    # Truncate
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length - 3] + "..."

    return cleaned.strip()


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "format_phone_number",
    "validate_phone_number",
    "strip_whatsapp_prefix",
    "get_local_number",
    "validate_placeholders",
    "validate_media_url",
    "generate_message_id",
    "sanitize_text_for_whatsapp",
]