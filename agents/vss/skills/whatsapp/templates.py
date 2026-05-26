"""
Templates — WhatsApp Template Management
=========================================
Manages all DoubleTick WhatsApp Business templates.
Enforces placeholder requirements and media validation.

Usage:
    from skills.whatsapp.templates import (
        TEMPLATES,
        get_template,
        validate_template_send,
        get_template_by_intent,
    )

    # Check what a template needs
    template = get_template("chat_support")
    print(template.variables)  # 1
    print(template.media_type)  # None

    # Validate before sending
    ok, error = validate_template_send("chat_support", ["Ramesh"], None)
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple

# ==============================================================================
# TEMPLATE DEFINITIONS
# ==============================================================================

@dataclass(frozen=True)
class WhatsAppTemplate:
    """
    Immutable template definition.
    Use TEMPLATES dict or get_template() to access.
    """
    name: str
    description: str
    media_type: Optional[str]  # None="text", "IMAGE", "DOCUMENT"
    required_variables: int  # 0 for no body variables
    default_media_url: Optional[str] = None
    language: str = "en"

    def validate_placeholders(self, placeholders: List[str]) -> Tuple[bool, str]:
        """Check if placeholders match template requirements."""
        if len(placeholders) < self.required_variables:
            return False, (
                f"'{self.name}' requires {self.required_variables} variable(s), "
                f"got {len(placeholders) if placeholders else 0}"
            )
        return True, ""


# All available templates
TEMPLATES: Dict[str, WhatsAppTemplate] = {
    # --- TEXT TEMPLATES (utility, high delivery) ---

    "chat_support": WhatsAppTemplate(
        name="chat_support",
        description=(
            "Simple text notification. Use for follow-ups, reminders, "
            "and general customer contact when no other template fits."
        ),
        media_type=None,
        required_variables=1,  # customer name or reference
        language="en",
    ),

    # --- IMAGE TEMPLATES ---

    "invoice": WhatsAppTemplate(
        name="invoice",
        description=(
            "Image with text overlay. Use for sending invoice images, "
            "quotations, or notification images with details."
        ),
        media_type="IMAGE",
        required_variables=3,  # invoiceid, date, GST details
        default_media_url="https://data-storage.doubletick.io/org_4NohhoUgic/templates/9c5cbff0-fcbe-4e9b-a996-dc1d93c52260.png",
        language="en",
    ),

    # --- DOCUMENT TEMPLATES ---

    "invoice_pdf": WhatsAppTemplate(
        name="invoice_pdf",
        description=(
            "PDF document. Use for sending proposals, contracts, "
            "formal invoices, and detailed documents."
        ),
        media_type="DOCUMENT",
        required_variables=0,  # no body variables
        default_media_url="https://data-storage.doubletick.io/org_4NohhoUgic/templates/6c123c5d-e532-42ca-a9c0-bb96ddd8bc03.pdf",
        language="en",
    ),
}

# ==============================================================================
# TEMPLATE LOOKUP
# ==============================================================================

def get_template(name: str) -> Optional[WhatsAppTemplate]:
    """Get a template by name. Returns None if not found."""
    return TEMPLATES.get(name)


def list_templates() -> List[WhatsAppTemplate]:
    """List all available templates."""
    return list(TEMPLATES.values())


def template_exists(name: str) -> bool:
    """Check if a template name exists."""
    return name in TEMPLATES


# ==============================================================================
# TEMPLATE VALIDATION
# ==============================================================================

def validate_template_send(
    template_name: str,
    placeholders: List[str] = None,
    media_url: str = None,
    media_type: str = None,
) -> Tuple[bool, str]:
    """
    Validate that a template send request is well-formed.

    Checks:
    - Template exists
    - Correct number of placeholders
    - Media provided if template requires it
    - Media type matches template definition

    Args:
        template_name: Template to validate
        placeholders: List of variable values for body placeholders
        media_url: Media URL (required for IMAGE/DOCUMENT templates)
        media_type: "IMAGE" or "DOCUMENT" (auto-detected from template if omitted)

    Returns:
        (is_valid, error_message)
    """
    placeholders = placeholders or []

    template = get_template(template_name)
    if not template:
        return False, f"Unknown template: '{template_name}'. Available: {', '.join(TEMPLATES.keys())}"

    # Validate placeholders
    valid, error = template.validate_placeholders(placeholders)
    if not valid:
        return False, error

    # Validate media requirements
    if template.media_type == "IMAGE":
        if not media_url:
            # Use default media URL if not provided
            media_url = template.default_media_url
        if not media_url:
            return False, f"Template '{template_name}' (IMAGE) requires a media_url"

    elif template.media_type == "DOCUMENT":
        if not media_url:
            media_url = template.default_media_url
        if not media_url:
            return False, f"Template '{template_name}' (DOCUMENT) requires a media_url"
        if not media_url.lower().endswith(".pdf"):
            return False, f"Template '{template_name}' (DOCUMENT) requires a .pdf URL"

    # Validate media type matches
    if media_url and media_type:
        if template.media_type and media_type != template.media_type:
            return False, (
                f"Template '{template_name}' requires media_type='{template.media_type}', "
                f"got '{media_type}'"
            )

    return True, ""


def get_template_by_intent(intent: str) -> str:
    """
    Map a business intent to the appropriate template.

    Args:
        intent: One of the defined intent strings

    Returns:
        Template name to use

    Raises:
        ValueError: If intent has no mapping
    """
    intent_map = {
        # Follow-up / reminder / notification
        "follow_up": "chat_support",
        "reminder": "chat_support",
        "notification": "chat_support",
        "general": "chat_support",
        "send_whatsapp": "chat_support",
        "inquiry_response": "chat_support",

        # Document sends
        "send_proposal": "invoice_pdf",
        "send_contract": "invoice_pdf",
        "send_invoice": "invoice_pdf",
        "send_pdf": "invoice_pdf",
        "document": "invoice_pdf",

        # Image sends
        "send_invoice_image": "invoice",
        "send_quotation": "invoice",
        "invoice_image": "invoice",
    }

    intent_lower = intent.lower().strip()
    if intent_lower not in intent_map:
        raise ValueError(
            f"No template mapping for intent '{intent}'. "
            f"Available intents: {', '.join(intent_map.keys())}"
        )

    return intent_map[intent_lower]


# ==============================================================================
# PLACEHOLDER HELPERS
# ==============================================================================

def build_placeholder_dict(template_name: str, **kwargs) -> List[str]:
    """
    Build a properly-ordered placeholder list from keyword arguments.

    Templates have ordered placeholders, not named ones.
    This helper lets you pass named args and get the ordered list.

    Example:
        placeholders = build_placeholder_dict(
            "invoice",
            invoice_id="INV-2024-001",
            invoice_date="2024-05-26",
            gst_details="GST: 29AAAAA0000A1Z5",
        )
        # Returns: ["INV-2024-001", "2024-05-26", "GST: 29AAAAA0000A1Z5"]

    Supported template placeholders:
    - chat_support: variable (customer name/reference)
    - invoice: invoice_id, invoice_date, gst_details
    """
    template = get_template(template_name)
    if not template:
        raise ValueError(f"Unknown template: {template_name}")

    if template.name == "chat_support":
        # Single variable: customer name or reference
        return [kwargs.get("variable", kwargs.get("customer_name", "Customer"))]

    elif template.name == "invoice":
        # 3 ordered variables
        return [
            kwargs.get("invoice_id", ""),
            kwargs.get("invoice_date", ""),
            kwargs.get("gst_details", ""),
        ]

    elif template.name == "invoice_pdf":
        # No body variables
        return []

    return []


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "WhatsAppTemplate",
    "TEMPLATES",
    "get_template",
    "list_templates",
    "template_exists",
    "validate_template_send",
    "get_template_by_intent",
    "build_placeholder_dict",
]