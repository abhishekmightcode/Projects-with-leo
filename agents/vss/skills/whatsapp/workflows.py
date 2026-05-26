"""
Workflows — High-Level WhatsApp Business Flows
================================================
Pre-built workflow functions for common VSS operations.
Each workflow handles the full business logic: window check → formatting → sending → CRM update.

Usage:
    from skills.whatsapp.workflows import send_followup, send_invoice, send_proposal

    result = send_followup(
        customer_name="Ramesh",
        variable="Ramesh",
    )
    print(result.success)  # True/False
"""

import logging
from typing import Optional, Dict, Any, List

from .client import DoubleTickClient, get_client
from .chat_window import ChatWindowChecker, get_checker
from .contacts import ContactResolver, get_resolver
from .templates import (
    get_template,
    validate_template_send,
    get_template_by_intent,
    build_placeholder_dict,
)
from .formatter import format_phone_number, sanitize_text_for_whatsapp, generate_message_id
from .memory import CustomerMemory, get_memory
from .exceptions import (
    ChatWindowClosedError,
    CustomerNotFoundError,
    TemplateValidationError,
    MediaValidationError,
    WorkflowError,
)

logger = logging.getLogger(__name__


# ==============================================================================
# WORKFLOW RESULT
# ==============================================================================

@dataclass
class WorkflowResult:
    """
    Result of a workflow execution.
    """
    success: bool
    method: str              # "text" or "template"
    template_name: Optional[str]
    message_id: Optional[str]
    phone: str
    customer_name: Optional[str]
    window_open: bool
    error: Optional[str]
    details: dict

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def failed(self) -> bool:
        return not self.success


# ==============================================================================
# BASE WORKFLOW CLASS
# ==============================================================================

class WhatsAppWorkflow:
    """
    Base class for WhatsApp workflows.

    Provides shared infrastructure:
    - client (DoubleTick API)
    - checker (chat window)
    - resolver (contacts)
    - memory (CRM)

    Subclass this to create custom workflows.
    """

    def __init__(
        self,
        client: DoubleTickClient = None,
        checker: ChatWindowChecker = None,
        resolver: ContactResolver = None,
        memory: CustomerMemory = None,
    ):
        self.client = client or get_client()
        self.checker = checker or get_checker()
        self.resolver = resolver or get_resolver()
        self.memory = memory or get_memory()

    def resolve_customer(self, identifier: str) -> tuple:
        """
        Resolve identifier to (phone, contact).
        Raises CustomerNotFoundError if not found.
        """
        contact = self.resolver.search(identifier)
        return contact.phone, contact

    def check_window(self, phone: str) -> bool:
        """Check if chat window is open."""
        status = self.checker.check(phone)
        return status.window_open

    def record_send(
        self,
        phone: str,
        method: str,
        template_name: Optional[str],
        message_id: Optional[str],
        placeholders: List[str],
        success: bool,
        customer_name: Optional[str] = None,
    ) -> None:
        """Record send in CRM memory."""
        try:
            content_preview = " ".join(placeholders) if placeholders else ""
            self.memory.record_outbound(
                phone=phone,
                method=method,
                placeholders=placeholders,
                template_name=template_name,
                message_id=message_id,
                content_preview=content_preview,
                success=success,
                name=customer_name,
            )
        except Exception as e:
            logger.error(f"Failed to record send in memory: {e}")


# ==============================================================================
# READY-MADE WORKFLOWS
# ==============================================================================

def send_followup(
    customer_identifier: str,
    variable: str = None,
    template_name: str = "chat_support",
    use_fallback: bool = True,
) -> WorkflowResult:
    """
    Send a follow-up message to a customer.

    Flow:
    1. Resolve customer name/phone to actual phone number
    2. Check chat window
    3. If window open: send free-form text
    4. If window closed: send chat_support template
    5. Record in CRM memory

    Args:
        customer_identifier: Customer name ("Ramesh") or phone
        variable: Template variable (usually customer name)
        template_name: Template to use (default: chat_support)
        use_fallback: If True, fallback to template if window closed

    Returns:
        WorkflowResult with success, message_id, etc.
    """
    wf = WhatsAppWorkflow()

    try:
        # Resolve customer
        phone, contact = wf.resolve_customer(customer_identifier)
        customer_name = contact.name
        variable = variable or customer_name or "Customer"

        # Check window
        window_open = wf.check_window(phone)

        message_id = None
        method = None
        sent_template = None

        if window_open and use_fallback:
            # Send free-form text
            text = f"Hi {variable}, following up on your inquiry with V Sustain Solar Solutions."
            text = sanitize_text_for_whatsapp(text)
            try:
                result = wf.client.send_text(to_phone=phone, text=text)
                message_id = result.get("message_id")
                method = "text"
            except Exception as e:
                if not use_fallback:
                    raise WorkflowError(f"Failed to send text: {e}")
                # Fall through to template
        else:
            # Window closed — send template
            placeholders = [variable]
            valid, err = validate_template_send(template_name, placeholders)
            if not valid:
                raise TemplateValidationError(template_name, 1, 0)

            result = wf.client.send_template(
                to_phone=phone,
                template_name=template_name,
                placeholders=placeholders,
            )
            message_id = result.get("message_id")
            method = "template"
            sent_template = template_name

        # Record in CRM
        wf.record_send(
            phone=phone,
            method=method,
            template_name=sent_template,
            message_id=message_id,
            placeholders=[variable],
            success=True,
            customer_name=customer_name,
        )

        return WorkflowResult(
            success=True,
            method=method,
            template_name=sent_template,
            message_id=message_id,
            phone=phone,
            customer_name=customer_name,
            window_open=window_open,
            error=None,
            details={"variable": variable},
        )

    except CustomerNotFoundError as e:
        return WorkflowResult(
            success=False,
            method=None,
            template_name=None,
            message_id=None,
            phone="",
            customer_name=None,
            window_open=False,
            error=f"Customer not found: {customer_identifier}",
            details={"identifier": customer_identifier},
        )

    except Exception as e:
        logger.error(f"send_followup failed: {e}")
        return WorkflowResult(
            success=False,
            method=None,
            template_name=None,
            message_id=None,
            phone="",
            customer_name=None,
            window_open=False,
            error=str(e),
            details={},
        )


def send_invoice(
    customer_identifier: str,
    invoice_id: str,
    invoice_date: str,
    gst_details: str,
    media_url: str = None,
) -> WorkflowResult:
    """
    Send an invoice image template to a customer.

    Requires 3 placeholders: invoice_id, invoice_date, gst_details

    Args:
        customer_identifier: Customer name or phone
        invoice_id: Invoice number (e.g., "INV-2024-001")
        invoice_date: Invoice date (e.g., "2024-05-26")
        gst_details: GST details line (e.g., "GST: 29AAAAA0000A1Z5")
        media_url: Image URL (uses DoubleTick default if not provided)
    """
    wf = WhatsAppWorkflow()

    try:
        phone, contact = wf.resolve_customer(customer_identifier)
        customer_name = contact.name

        placeholders = [invoice_id, invoice_date, gst_details]
        valid, err = validate_template_send("invoice", placeholders, media_url)
        if not valid:
            raise TemplateValidationError("invoice", 3, len(placeholders))

        result = wf.client.send_template(
            to_phone=phone,
            template_name="invoice",
            placeholders=placeholders,
            media_url=media_url,
            media_type="IMAGE",
        )

        wf.record_send(
            phone=phone,
            method="template",
            template_name="invoice",
            message_id=result.get("message_id"),
            placeholders=placeholders,
            success=True,
            customer_name=customer_name,
        )

        return WorkflowResult(
            success=True,
            method="template",
            template_name="invoice",
            message_id=result.get("message_id"),
            phone=phone,
            customer_name=customer_name,
            window_open=False,
            error=None,
            details={"invoice_id": invoice_id},
        )

    except CustomerNotFoundError as e:
        return WorkflowResult(success=False, method=None, template_name=None,
            message_id=None, phone="", customer_name=None, window_open=False,
            error=f"Customer not found: {customer_identifier}", details={})
    except Exception as e:
        logger.error(f"send_invoice failed: {e}")
        return WorkflowResult(success=False, method=None, template_name=None,
            message_id=None, phone="", customer_name=None, window_open=False,
            error=str(e), details={})


def send_proposal(
    customer_identifier: str,
    pdf_url: str = None,
) -> WorkflowResult:
    """
    Send a PDF proposal/document to a customer.

    Args:
        customer_identifier: Customer name or phone
        pdf_url: URL of the PDF (uses DoubleTick default if not provided)
    """
    wf = WhatsAppWorkflow()

    try:
        phone, contact = wf.resolve_customer(customer_identifier)
        customer_name = contact.name

        template = get_template("invoice_pdf")
        effective_url = pdf_url or template.default_media_url

        valid, err = validate_template_send("invoice_pdf", [], effective_url)
        if not valid:
            raise MediaValidationError("invoice_pdf", "DOCUMENT", err)

        result = wf.client.send_template(
            to_phone=phone,
            template_name="invoice_pdf",
            placeholders=[],
            media_url=effective_url,
            media_type="DOCUMENT",
        )

        wf.record_send(
            phone=phone,
            method="template",
            template_name="invoice_pdf",
            message_id=result.get("message_id"),
            placeholders=[],
            success=True,
            customer_name=customer_name,
        )

        return WorkflowResult(
            success=True,
            method="template",
            template_name="invoice_pdf",
            message_id=result.get("message_id"),
            phone=phone,
            customer_name=customer_name,
            window_open=False,
            error=None,
            details={},
        )

    except CustomerNotFoundError:
        return WorkflowResult(success=False, method=None, template_name=None,
            message_id=None, phone="", customer_name=None, window_open=False,
            error=f"Customer not found: {customer_identifier}", details={})
    except Exception as e:
        logger.error(f"send_proposal failed: {e}")
        return WorkflowResult(success=False, method=None, template_name=None,
            message_id=None, phone="", customer_name=None, window_open=False,
            error=str(e), details={})


def send_support_message(
    customer_identifier: str,
    message_text: str,
) -> WorkflowResult:
    """
    Smart send: auto-selects text vs template based on window.

    Use this for ad-hoc messages where you don't know the window status.

    Args:
        customer_identifier: Customer name or phone
        message_text: The message to send (used as template variable if template used)
    """
    wf = WhatsAppWorkflow()

    try:
        phone, contact = wf.resolve_customer(customer_identifier)
        customer_name = contact.name

        window_open = wf.check_window(phone)
        message_id = None
        method = None
        template_name = None

        if window_open:
            # Try free-form text
            sanitized = sanitize_text_for_whatsapp(message_text)
            try:
                result = wf.client.send_text(to_phone=phone, text=sanitized)
                message_id = result.get("message_id")
                method = "text"
            except Exception:
                # Fall back to template
                method = "template"
                template_name = "chat_support"
        else:
            method = "template"
            template_name = "chat_support"

        if method == "template":
            # Use first 50 chars as variable
            variable = message_text[:50].strip()
            placeholders = [variable or customer_name or "Customer"]
            result = wf.client.send_template(
                to_phone=phone,
                template_name=template_name,
                placeholders=placeholders,
            )
            message_id = result.get("message_id")

        wf.record_send(
            phone=phone,
            method=method,
            template_name=template_name,
            message_id=message_id,
            placeholders=[message_text[:50]],
            success=True,
            customer_name=customer_name,
        )

        return WorkflowResult(
            success=True,
            method=method,
            template_name=template_name,
            message_id=message_id,
            phone=phone,
            customer_name=customer_name,
            window_open=window_open,
            error=None,
            details={},
        )

    except CustomerNotFoundError:
        return WorkflowResult(success=False, method=None, template_name=None,
            message_id=None, phone="", customer_name=None, window_open=False,
            error=f"Customer not found: {customer_identifier}", details={})
    except Exception as e:
        logger.error(f"send_support_message failed: {e}")
        return WorkflowResult(success=False, method=None, template_name=None,
            message_id=None, phone="", customer_name=None, window_open=False,
            error=str(e), details={})


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "WorkflowResult",
    "WhatsAppWorkflow",
    "send_followup",
    "send_invoice",
    "send_proposal",
    "send_support_message",
]