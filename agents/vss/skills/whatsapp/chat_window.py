"""
Chat Window — 24-Hour Window Logic
====================================
Manages the WhatsApp Business 24-hour chat window rule.
Determines whether to use template messages or free-form text.

Usage:
    from skills.whatsapp.chat_window import ChatWindowChecker, should_use_template

    checker = ChatWindowChecker()
    result = checker.check("919876543210")

    if result.window_open:
        # Can send free-form text
        client.send_text(to_phone, "Hello Ramesh!")
    else:
        # Must use template message
        send_template(to_phone, "chat_support", ["Ramesh"])
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .client import DoubleTickClient, get_client
from .formatter import format_phone_number, validate_phone_number
from .exceptions import ChatWindowAPIError

logger = logging.getLogger(__name__)


# ==============================================================================
# RESULT DATACLASS
# ==============================================================================

@dataclass
class WindowStatus:
    """
    Result of a chat window check.
    """
    window_open: bool
    last_reply_at: Optional[str]
    message: str
    phone: str
    raw_response: Optional[dict] = None

    def __bool__(self) -> bool:
        """Allow direct truthiness check: if window_status: ... """
        return self.window_open

    def to_dict(self) -> dict:
        return {
            "window_open": self.window_open,
            "last_reply_at": self.last_reply_at,
            "message": self.message,
            "phone": self.phone,
        }


# ==============================================================================
# CHAT WINDOW CHECKER
# ==============================================================================

class ChatWindowChecker:
    """
    Checks and caches 24-hour chat window status for customers.

    The 24-hour rule:
    - If customer has replied within 24 hours → window OPEN → free-form text allowed
    - If no reply in 24 hours → window CLOSED → must use template message

    This class provides caching to avoid redundant API calls within a session.
    """

    def __init__(self, client: Optional[DoubleTickClient] = None, cache_ttl_seconds: int = 300):
        """
        Args:
            client: DoubleTick client to use. Uses global default if None.
            cache_ttl_seconds: How long to cache window status (default: 5 min)
        """
        self.client = client or get_client()
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, tuple] = {}  # phone → (WindowStatus, timestamp)

    def check(self, phone: str, use_cache: bool = True) -> WindowStatus:
        """
        Check if 24-hour chat window is open for a customer.

        Args:
            phone: Customer phone (any format, will be formatted)
            use_cache: Use cached result if within TTL

        Returns:
            WindowStatus object

        Raises:
            ChatWindowAPIError: If the API call fails
        """
        try:
            formatted = format_phone_number(phone)
        except ValueError:
            raise ChatWindowAPIError(phone=phone, reason="Invalid phone number format")

        # Check cache
        if use_cache and formatted in self._cache:
            status, cached_at = self._cache[formatted]
            import time
            if time.time() - cached_at < self.cache_ttl:
                logger.debug(f"Chat window cache hit for {formatted}")
                return status

        # Call API
        logger.info(f"Checking chat window for {formatted}")
        result = self.client.check_chat_window(formatted)

        status = WindowStatus(
            window_open=result["window_open"],
            last_reply_at=result.get("last_reply_at"),
            message=result["message"],
            phone=formatted,
            raw_response=result.get("raw_response"),
        )

        # Update cache
        import time
        self._cache[formatted] = (status, time.time())

        return status

    def is_open(self, phone: str) -> bool:
        """Quick check: returns True if window is open."""
        return self.check(phone).window_open

    def clear_cache(self, phone: Optional[str] = None) -> None:
        """Clear cached window status for a phone, or all if phone is None."""
        if phone:
            formatted = format_phone_number(phone)
            self._cache.pop(formatted, None)
        else:
            self._cache.clear()

    def bulk_check(self, phones: list) -> Dict[str, WindowStatus]:
        """
        Check window status for multiple phones.

        Returns:
            Dict mapping phone → WindowStatus
        """
        results = {}
        for phone in phones:
            try:
                results[phone] = self.check(phone)
            except ChatWindowAPIError as e:
                logger.error(f"Failed to check {phone}: {e}")
                results[phone] = WindowStatus(
                    window_open=False,
                    last_reply_at=None,
                    message=f"Error: {e}",
                    phone=phone,
                )
        return results


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

_default_checker: Optional[ChatWindowChecker] = None


def get_checker() -> ChatWindowChecker:
    """Get or create the default ChatWindowChecker."""
    global _default_checker
    if _default_checker is None:
        _default_checker = ChatWindowChecker()
    return _default_checker


def check_window(phone: str) -> WindowStatus:
    """One-shot window check using default checker."""
    return get_checker().check(phone)


def should_use_template(phone: str) -> bool:
    """
    Quick decision helper: should I use a template or text?

    Returns:
        True → use template (window closed or unknown)
        False → free-form text is OK (window open)
    """
    try:
        status = check_window(phone)
        return not status.window_open
    except ChatWindowAPIError:
        # On error, be conservative — use template
        return True


def can_send_text(phone: str) -> bool:
    """Quick check: can free-form text be sent right now?"""
    try:
        return check_window(phone).window_open
    except ChatWindowAPIError:
        return False


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "WindowStatus",
    "ChatWindowChecker",
    "get_checker",
    "check_window",
    "should_use_template",
    "can_send_text",
]