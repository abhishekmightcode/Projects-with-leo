"""
Client — DoubleTick API Client
==============================
Low-level HTTP client for DoubleTick WhatsApp Business API.
Handles retries, auth, timeouts, and raw API calls.

DO NOT hardcode API keys — use environment variables via config.py.

Usage:
    from skills.whatsapp.client import DoubleTickClient, send_template, send_text

    client = DoubleTickClient()
    result = client.send_template(to="919876543210", template_name="chat_support", ...)
"""

import os
import logging
import time
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode

from .config import (
    DOUBLETICK_API_KEY,
    DOUBLETICK_BASE_URL,
    WABA_NUMBER,
    DEFAULT_TIMEOUT_SECONDS,
    CHAT_WINDOW_TIMEOUT,
)
from .exceptions import (
    APIError,
    APITimeoutError,
    MissingAPIKeyError,
    raise_from_response,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# CLIENT
# ==============================================================================

class DoubleTickClient:
    """
    Low-level DoubleTick API client.

    Handles:
    - Auth headers (from env)
    - Request retries with exponential backoff
    - Timeout management
    - Response parsing
    - Error wrapping

    This is a thin, dumb client. No business logic here.
    Business logic belongs in workflows.py and processor.py.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        waba_number: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = 2,
    ):
        self.api_key = api_key or DOUBLETICK_API_KEY
        self.waba_number = waba_number or WABA_NUMBER
        self.base_url = base_url or DOUBLETICK_BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries

        if not self.api_key:
            raise MissingAPIKeyError(
                "DOUBLETICK_API_KEY not set. "
                "Set it in environment before using the client."
            )

        self._session = requests.Session()
        self._session.headers.update(self._build_headers())

    def _build_headers(self) -> dict:
        """Build auth and content headers."""
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # --------------------------------------------------------------------------
    # CORE HTTP METHODS
    # --------------------------------------------------------------------------

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        json: dict = None,
        timeout: Optional[int] = None,
        retry_count: int = 0,
    ) -> dict:
        """
        Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (appended to base_url)
            params: URL query parameters (for GET calls)
            json: JSON body (for POST calls)
            timeout: Per-request timeout override
            retry_count: Current retry attempt (internal)

        Returns:
            Parsed JSON response dict

        Raises:
            APIError: On non-2xx response or after all retries exhausted
            APITimeoutError: On timeout
        """
        url = f"{self.base_url}{endpoint}"
        timeout = timeout or self.timeout

        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"[{method}] {url} attempt {attempt + 1}")

                if method.upper() == "GET":
                    response = self._session.get(url, params=params, timeout=timeout)
                elif method.upper() == "POST":
                    response = self._session.post(url, json=json, timeout=timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status_code in (200, 201):
                    return response.json()

                # Non-retryable: 4xx client errors (except 429)
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    try:
                        data = response.json()
                    except Exception:
                        data = {"raw": response.text}
                    raise_from_response(data, response.status_code)

                # Retryable: 5xx server errors or 429 Too Many Requests
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(f"API error attempt {attempt + 1}: {last_error}")

            except requests.exceptions.Timeout:
                last_error = f"Timeout after {timeout}s (attempt {attempt + 1})"
                logger.warning(last_error)

            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {str(e)[:100]} (attempt {attempt + 1})"
                logger.warning(last_error)

            # Wait before retry — exponential backoff
            if attempt < self.max_retries:
                wait = (2 ** attempt) + (0.1 * attempt)  # 2s, 4.1s, 8.2s
                logger.info(f"Retrying in {wait:.1f}s...")
                time.sleep(wait)

        # All retries exhausted
        raise APIError(
            status_code=None,
            message=f"Request failed after {self.max_retries + 1} attempts. Last error: {last_error}",
        )

    def get(self, endpoint: str, params: dict = None, timeout: int = None) -> dict:
        """Make a GET request."""
        return self._request("GET", endpoint, params=params, timeout=timeout)

    def post(self, endpoint: str, json: dict = None, timeout: int = None) -> dict:
        """Make a POST request."""
        return self._request("POST", endpoint, json=json, timeout=timeout)

    # --------------------------------------------------------------------------
    # CHAT WINDOW
    # --------------------------------------------------------------------------

    def check_chat_window(self, customer_phone: str) -> dict:
        """
        Check if the 24-hour chat window is open for a customer.

        Args:
            customer_phone: Customer number in 91XXXXXXXXXX format

        Returns:
            {
                "window_open": bool,
                "last_reply_at": str or None,
                "message": str,
                "raw_response": dict
            }
        """
        params = {
            "wabaPhone": self.waba_number,
            "customerPhone": customer_phone,
        }

        try:
            data = self.get(
                "/whatsapp/chatwindow/status",
                params=params,
                timeout=CHAT_WINDOW_TIMEOUT,
            )
        except APIError as e:
            # Conservative fallback: treat as window closed
            logger.warning(f"Chat window check failed: {e}. Defaulting to closed.")
            return {
                "window_open": False,
                "last_reply_at": None,
                "message": f"API error: {e}",
                "raw_response": None,
            }

        last_reply = data.get("lastReplyAt") or data.get("lastReply")
        window_open = last_reply is not None

        return {
            "window_open": window_open,
            "last_reply_at": last_reply,
            "message": "Window open" if window_open else "Window closed",
            "raw_response": data,
        }

    # --------------------------------------------------------------------------
    # MESSAGES — TEMPLATE
    # --------------------------------------------------------------------------

    def send_template(
        self,
        to_phone: str,
        template_name: str,
        language: str = "en",
        placeholders: List[str] = None,
        media_url: str = None,
        media_type: str = None,
        filename: str = None,
    ) -> dict:
        """
        Send a template message.

        Args:
            to_phone: Recipient in 91XXXXXXXXXX format
            template_name: Name of template in DoubleTick (e.g., "chat_support")
            language: Template language (default: "en")
            placeholders: List of placeholder values for body variables
            media_url: URL for IMAGE/DOCUMENT header (optional)
            media_type: "IMAGE" or "DOCUMENT" (required if media_url provided)
            filename: Filename for the media (optional, auto-extracted if omitted)

        Returns:
            {"success": bool, "message_id": str, "recipient": str, "response": dict}
        """
        # Build template data structure
        template_data = {
            "body": {
                "placeholders": placeholders or [],
            }
        }

        # Add media header if provided
        if media_url:
            if not media_type:
                raise ValueError("media_type required when media_url is provided")
            template_data["header"] = {
                "type": media_type,
                "mediaUrl": media_url,
                "filename": filename or media_url.split("/")[-1],
            }

        payload = {
            "messages": [{
                "to": to_phone,
                "from": self.waba_number,
                "content": {
                    "templateName": template_name,
                    "language": language,
                    "templateData": template_data,
                }
            }]
        }

        data = self.post("/whatsapp/message/template", json=payload)

        return {
            "success": True,
            "message_id": data.get("messageId") or data.get("id"),
            "recipient": to_phone,
            "response": data,
        }

    # --------------------------------------------------------------------------
    # MESSAGES — FREE-FORM TEXT
    # --------------------------------------------------------------------------

    def send_text(
        self,
        to_phone: str,
        text: str,
        message_id: str = None,
    ) -> dict:
        """
        Send a free-form text message.

        WARNING: Only works if 24-hour chat window is open for this customer.
        Use check_chat_window() first, or use workflows.smart_send() which handles this.

        Args:
            to_phone: Recipient in 91XXXXXXXXXX format
            text: Message text
            message_id: Optional custom message ID

        Returns:
            {"success": bool, "message_id": str, "recipient": str, "response": dict}
        """
        payload = {
            "messages": [{
                "to": to_phone,
                "from": self.waba_number,
                "content": {"text": text},
            }]
        }

        if message_id:
            payload["messages"][0]["messageId"] = message_id

        data = self.post("/whatsapp/message/text", json=payload)

        return {
            "success": True,
            "message_id": data.get("messageId") or data.get("id"),
            "recipient": to_phone,
            "response": data,
        }

    # --------------------------------------------------------------------------
    # UTILITY
    # --------------------------------------------------------------------------

    def get_customer(self, customer_phone: str) -> dict:
        """Get customer details from DoubleTick."""
        params = {
            "phone": customer_phone,
            "wabaPhone": self.waba_number,
        }
        return self.get("/v2/customers", params=params)

    def get_templates(self) -> dict:
        """Get list of available templates."""
        return self.get("/v2/templates")


# ==============================================================================
# CONVENIENCE FUNCTIONS — one-shot API calls
# ==============================================================================

# Lazy-initialized client (created on first use)
_client: Optional[DoubleTickClient] = None


def get_client() -> DoubleTickClient:
    """Get or create the shared DoubleTick client instance."""
    global _client
    if _client is None:
        _client = DoubleTickClient()
    return _client


def send_template(
    to_phone: str,
    template_name: str,
    language: str = "en",
    placeholders: List[str] = None,
    media_url: str = None,
    media_type: str = None,
) -> dict:
    """One-shot template send using default client."""
    return get_client().send_template(
        to_phone=to_phone,
        template_name=template_name,
        language=language,
        placeholders=placeholders,
        media_url=media_url,
        media_type=media_type,
    )


def send_text(to_phone: str, text: str) -> dict:
    """One-shot text send using default client."""
    return get_client().send_text(to_phone=to_phone, text=text)


def check_chat_window(customer_phone: str) -> dict:
    """One-shot chat window check using default client."""
    return get_client().check_chat_window(customer_phone)