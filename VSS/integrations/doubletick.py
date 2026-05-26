"""
VSS DoubleTick WhatsApp Integration
====================================
Handles all WhatsApp messaging for VSS (V Sustain Solar Solutions) via DoubleTick API.
Pravesh (VSS owner) talks to the agent on Telegram → Agent sends WhatsApp to customers.
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List

# ==============================================================================
# CONFIGURATION
# ==============================================================================

DOUBLETICK_API_KEY = "key_RueP4Mjgc6knJLGTgRzXP7gAejGGxvyQsgzqd7M8QCtim3oRWIBJKxnYdPUhU2h7CAF1sT52KCzM9E6RfDpk1tN5B9WHFaMcKLIq76uM4ZSrv71tYFe0A2nRTzvb0gy1vwSFr2VYysbdDOkppPmNp7QZTBEPKDf4CzFCaaXCNNojzpF8gGGFzQULattW8wnErspoYkL5ffnQaNDKdc1yINDaaNEODI7jTmrvVndZUzwidj7bqufFis0r7ssn"
WABA_NUMBER = "919900108067"  # Country code 91 + number 9900108067, no + prefix
BASE_URL = "https://public.doubletick.io"

HEADERS = {
    "Authorization": DOUBLETICK_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# ==============================================================================
# PHONE NUMBER VALIDATION & FORMATTING
# ==============================================================================

def format_phone_number(phone: str) -> str:
    """
    Format phone number to Indian format (91 + 10 digits, no + prefix).
    
    Examples:
        9876543210     → 919876543210
        +91 9876543210 → 919876543210
        919876543210   → 919876543210
    
    Args:
        phone: Raw phone input (various formats)
    
    Returns:
        Formatted number: 91XXXXXXXXXX (no +)
    
    Raises:
        ValueError: If phone cannot be parsed to valid Indian format
    """
    # Strip all non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Handle +91 prefix
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]  # Remove 91 prefix for re-addition below
    
    # Must be exactly 10 digits now
    if len(digits) != 10:
        raise ValueError(f"Invalid phone number: {phone}. Expected 10 digits, got {len(digits)}")
    
    return f"91{digits}"


def validate_phone(phone: str) -> bool:
    """Check if phone can be formatted to valid Indian number."""
    try:
        format_phone_number(phone)
        return True
    except ValueError:
        return False


# ==============================================================================
# CHAT WINDOW STATUS CHECK
# ==============================================================================

def check_chat_window_status(to_phone: str) -> Dict[str, Any]:
    """
    Check if 24-hour chat window is open for a customer.
    
    Args:
        to_phone: Customer phone (various formats, will be auto-formatted)
    
    Returns:
        {"window_open": bool, "message": str, "last_reply_at": str or None}
    """
    try:
        formatted_to = format_phone_number(to_phone)
    except ValueError as e:
        return {"window_open": False, "message": str(e), "last_reply_at": None}
    
    url = f"{BASE_URL}/whatsapp/chatwindow/status"
    params = {
        "wabaPhone": WABA_NUMBER,
        "customerPhone": formatted_to
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # DoubleTick returns status in various formats; assume window is open if last_reply exists
            last_reply = data.get("lastReplyAt") or data.get("lastReply")
            window_open = last_reply is not None
            return {
                "window_open": window_open,
                "message": "Window open" if window_open else "Window closed - use template message",
                "last_reply_at": last_reply,
                "raw_response": data
            }
        else:
            # If API fails, default to conservative (use template)
            return {
                "window_open": False,
                "message": f"API error {response.status_code}: {response.text}",
                "last_reply_at": None,
                "raw_response": None
            }
    except Exception as e:
        return {
            "window_open": False,
            "message": f"Connection error: {str(e)}",
            "last_reply_at": None,
            "raw_response": None
        }


# ==============================================================================
# SEND TEMPLATE MESSAGES
# ==============================================================================

def send_template_message(
    to_phone: str,
    template_name: str,
    language: str = "en",
    template_data: Optional[Dict[str, Any]] = None,
    media_url: Optional[str] = None,
    media_type: Optional[str] = None,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a template message via DoubleTick.
    
    Args:
        to_phone: Customer phone (various formats, auto-formatted)
        template_name: Name of the template in DoubleTick (e.g., "invoice", "chat_support")
        language: Template language code (default: "en")
        template_data: Dict with "body" → {"placeholders": [values]} for text variables
        media_url: Optional media URL for image/doc templates
        media_type: "IMAGE" or "DOCUMENT" if media present
        filename: Filename for the media
    
    Returns:
        {"success": bool, "message_id": str or None, "error": str or None}
    """
    try:
        formatted_to = format_phone_number(to_phone)
    except ValueError as e:
        return {"success": False, "message_id": None, "error": str(e)}
    
    url = f"{BASE_URL}/whatsapp/message/template"
    
    # Build content structure
    content = {
        "templateName": template_name,
        "language": language,
        "templateData": {
            "body": {
                "placeholders": template_data.get("body", {}).get("placeholders", []) if template_data else []
            }
        }
    }
    
    # Add header with media if provided
    if media_url:
        content["templateData"]["header"] = {
            "type": media_type or "IMAGE",
            "mediaUrl": media_url,
            "filename": filename or media_url.split("/")[-1]
        }
    
    payload = {
        "messages": [{
            "to": formatted_to,
            "from": WABA_NUMBER,
            "content": content
        }]
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=15)
        result = response.json()
        
        if response.status_code in (200, 201):
            return {
                "success": True,
                "message_id": result.get("messageId") or result.get("id"),
                "recipient": formatted_to,
                "response": result
            }
        else:
            return {
                "success": False,
                "message_id": None,
                "error": result.get("message", result.get("error", response.text)),
                "status_code": response.status_code
            }
    except Exception as e:
        return {"success": False, "message_id": None, "error": str(e)}


# ==============================================================================
# SEND FREE-FORM TEXT (24-hour window must be open)
# ==============================================================================

def send_text_message(to_phone: str, text: str, message_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a free-form text message. Only works if 24-hour window is open.
    
    Args:
        to_phone: Customer phone (various formats, auto-formatted)
        text: Message text to send
        message_id: Optional custom message ID (UUID v4)
    
    Returns:
        {"success": bool, "message_id": str or None, "error": str or None}
    """
    try:
        formatted_to = format_phone_number(to_phone)
    except ValueError as e:
        return {"success": False, "message_id": None, "error": str(e)}
    
    # Check window first
    window_status = check_chat_window_status(formatted_to)
    if not window_status.get("window_open"):
        return {
            "success": False,
            "message_id": None,
            "error": "Chat window is closed. Customer hasn't replied in 24 hours. Use send_template_message() instead.",
            "window_status": window_status
        }
    
    url = f"{BASE_URL}/whatsapp/message/text"
    
    payload = {
        "messages": [{
            "to": formatted_to,
            "from": WABA_NUMBER,
            "content": {"text": text}
        }]
    }
    
    if message_id:
        payload["messages"][0]["messageId"] = message_id
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=15)
        result = response.json()
        
        if response.status_code in (200, 201):
            return {
                "success": True,
                "message_id": result.get("messageId") or result.get("id"),
                "recipient": formatted_to,
                "response": result
            }
        else:
            return {
                "success": False,
                "message_id": None,
                "error": result.get("message", result.get("error", response.text)),
                "status_code": response.status_code
            }
    except Exception as e:
        return {"success": False, "message_id": None, "error": str(e)}


# ==============================================================================
# WRAPPER: SMART SEND (auto-selects template vs text based on window)
# ==============================================================================

def send_message(
    to_phone: str,
    text: str,
    use_template_fallback: bool = True,
    template_name: str = "chat_support",
    template_variables: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Smart message sender: tries text if window open, falls back to template.
    
    Args:
        to_phone: Customer phone (various formats, auto-formatted)
        text: Message text to send
        use_template_fallback: If True, send template when window closed
        template_name: Template to use for fallback (default: chat_support)
        template_variables: Variables for the template (e.g., [customer_name])
    
    Returns:
        {"success": bool, "method": "text"|"template", "message_id": str, "error": str or None}
    """
    # First check window status
    window_status = check_chat_window_status(to_phone)
    
    if window_status.get("window_open"):
        # Try free-form text
        result = send_text_message(to_phone, text)
        if result["success"]:
            return {**result, "method": "text"}
        # If text fails, try template as fallback
        if use_template_fallback:
            pass  # Fall through to template
        else:
            return {**result, "method": "text", "fallback_error": True}
    
    # Window closed — use template
    if use_template_fallback:
        vars = template_variables or [text[:50]]  # Use first 50 chars as variable if none given
        result = send_template_message(
            to_phone=to_phone,
            template_name=template_name,
            template_data={"body": {"placeholders": vars}}
        )
        return {**result, "method": "template"}
    
    return {
        "success": False,
        "method": None,
        "message_id": None,
        "error": "Chat window closed and template fallback disabled"
    }


# ==============================================================================
# TEMPLATE-SPECIFIC SENDERS
# ==============================================================================

def send_invoice_template(
    to_phone: str,
    invoice_id: str,
    invoice_date: str,
    gst_details: str,
    media_url: str = "https://data-storage.doubletick.io/org_4NohhoUgic/templates/9c5cbff0-fcbe-4e9b-a996-dc1d93c52260.png"
) -> Dict[str, Any]:
    """Send invoice template with image + 3 variables."""
    return send_template_message(
        to_phone=to_phone,
        template_name="invoice",
        media_url=media_url,
        media_type="IMAGE",
        filename=media_url.split("/")[-1],
        template_data={
            "body": {
                "placeholders": [invoice_id, invoice_date, gst_details]
            }
        }
    )


def send_pdf_template(
    to_phone: str,
    pdf_url: str = "https://data-storage.doubletick.io/org_4NohhoUgic/templates/6c123c5d-e532-42ca-a9c0-bb96ddd8bc03.pdf"
) -> Dict[str, Any]:
    """Send PDF document template (no variables)."""
    return send_template_message(
        to_phone=to_phone,
        template_name="invoice_pdf",
        media_url=pdf_url,
        media_type="DOCUMENT",
        filename=pdf_url.split("/")[-1]
    )


def send_chat_support_template(
    to_phone: str,
    variable: str = "Customer"
) -> Dict[str, Any]:
    """Send simple text template with 1 variable."""
    return send_template_message(
        to_phone=to_phone,
        template_name="chat_support",
        template_data={"body": {"placeholders": [variable]}}
    )


# ==============================================================================
# CONTACT LOOKUP (Google Contacts integration)
# ==============================================================================

GOOGLE_REFRESH_TOKEN = "1//0gS"  # Stored separately - see VSS Google OAuth config

def get_access_token() -> Optional[str]:
    """Refresh Google OAuth access token."""
    import google.auth.transport.requests
    # This would use the stored refresh token to get a fresh access token
    # For now, return None — actual implementation needs OAuth flow completion
    return None  # TODO: Implement token refresh


# ==============================================================================
# TEST FUNCTION
# ==============================================================================

if __name__ == "__main__":
    # Test phone formatting
    test_phones = ["9876543210", "+91 9876543210", "919876543210", "8765432109"]
    print("Phone Format Tests:")
    for ph in test_phones:
        try:
            print(f"  {ph} → {format_phone_number(ph)}")
        except ValueError as e:
            print(f"  {ph} → ERROR: {e}")
    
    print("\n" + "="*50)
    print("VSS DoubleTick Integration loaded successfully.")
    print(f"WABA Number: {WABA_NUMBER}")
    print(f"Base URL: {BASE_URL}")