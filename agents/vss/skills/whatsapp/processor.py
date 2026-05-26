"""
Processor — VSustainAI WhatsApp Intent Processing
====================================================
Routes incoming Telegram messages (voice or text) from Pravesh
to the appropriate WhatsApp workflow.

This is the brain of VSustainAI's WhatsApp capability.
It understands what Pravesh wants and executes the right workflow.

Usage:
    from skills.whatsapp.processor import WhatsAppProcessor

    processor = WhatsAppProcessor()
    result = processor.route("send a message to Ramesh about his pending payment")
    print(result.success)
"""

import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

from .workflows import (
    WhatsAppWorkflow,
    send_followup,
    send_invoice,
    send_proposal,
    send_support_message,
    WorkflowResult,
)
from .contacts import get_resolver, ContactResolver
from .memory import get_memory
from .exceptions import CustomerNotFoundError

logger = logging.getLogger(__name__)


# ==============================================================================
# INTENT DEFINITIONS
# ==============================================================================

@dataclass
class IntentResult:
    """
    Parsed intent from Pravesh's message.
    """
    intent: str             # e.g., "send_whatsapp", "send_invoice"
    customer_name: Optional[str]  # e.g., "Ramesh"
    message_text: Optional[str]  # e.g., "about his pending payment"
    extracted_vars: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # 0.0 to 1.0

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "customer_name": self.customer_name,
            "message_text": self.message_text,
            "extracted_vars": self.extracted_vars,
            "confidence": self.confidence,
        }


# ==============================================================================
# INTENT PATTERNS
# ==============================================================================

INTENT_PATTERNS = {
    "send_whatsapp": [
        r"send\s+(?:a\s+)?(?:whatsapp\s+)?(?:message\s+)?to\s+(\w+)",
        r"whatsapp\s+(\w+)",
        r"message\s+to\s+(\w+)",
        r"text\s+(\w+)",
        r"send\s+(\w+)\s+about",
        r"contact\s+(\w+)",
    ],
    "send_invoice": [
        r"send\s+(?:the\s+)?invoice",
        r"invoice\s+(?:to\s+)?(\w+)",
        r"send\s+invoice\s+to\s+(\w+)",
    ],
    "send_proposal": [
        r"send\s+(?:the\s+)?proposal",
        r"send\s+(?:the\s+)?pdf",
        r"proposal\s+(?:to\s+)?(\w+)",
        r"send\s+proposal\s+to\s+(\w+)",
    ],
    "follow_up": [
        r"follow\s+up",
        r"followup",
        r"chase\s+(\w+)",
        r"pending\s+(?:payment\s+)?(?:for\s+)?(\w+)",
        r"remind\s+(\w+)",
    ],
    "price_quote": [
        r"price\s+quote",
        r"quote\s+(?:for\s+)?(\w+)",
        r"how\s+much",
        r"kva\s+price",
        r"system\s+price",
    ],
    "site_visit": [
        r"site\s+visit",
        r"schedule\s+visit",
        r"installation",
        r"visit\s+(\w+)",
    ],
    "update_crm": [
        r"update\s+(?:the\s+)?crm",
        r"add\s+to\s+crm",
        r"log\s+in\s+crm",
        r"record\s+(\w+)",
    ],
    "general": [],  # Fallback intent
}


# ==============================================================================
# PROCESSOR
# ==============================================================================

class WhatsAppProcessor:
    """
    VSustainAI's WhatsApp brain.

    Receives Pravesh's Telegram message → parses intent → executes workflow → returns result.

    Key responsibilities:
    - Parse customer name from Pravesh's instruction
    - Classify intent (send_whatsapp, invoice, follow_up, etc.)
    - Extract additional entities (amounts, dates, invoice IDs)
    - Execute the appropriate workflow
    - Return structured result for Telegram confirmation

    Voice notes go through STT first (stt_integration.py), then here.
    """

    def __init__(
        self,
        resolver: ContactResolver = None,
    ):
        self.resolver = resolver or get_resolver()

    # --------------------------------------------------------------------------
    # PARSING
    # --------------------------------------------------------------------------

    def parse(self, text: str) -> IntentResult:
        """
        Parse Pravesh's text instruction into structured intent.

        Args:
            text: The raw message, e.g., "send a message to Ramesh about his pending payment"

        Returns:
            IntentResult with intent, customer_name, message_text, extracted_vars
        """
        text_lower = text.lower().strip()

        # Try each intent pattern
        for intent, patterns in INTENT_PATTERNS.items():
            if intent == "general":
                continue

            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    customer_name = match.group(1).title() if match.groups() else None

                    return IntentResult(
                        intent=intent,
                        customer_name=customer_name,
                        message_text=text,
                        extracted_vars={},
                        confidence=0.9,
                    )

        # Fallback: general intent
        return IntentResult(
            intent="general",
            customer_name=self._extract_name_fallback(text_lower),
            message_text=text,
            extracted_vars={},
            confidence=0.5,
        )

    def _extract_name_fallback(self, text: str) -> Optional[str]:
        """
        Try to extract a name even without clear intent patterns.
        Looks for capitalized words that might be names.
        """
        # Simple heuristic: look for word after "to", "for", "about"
        patterns = [
            r"\bto\s+([A-Z][a-z]+)",
            r"\bfor\s+([A-Z][a-z]+)",
            r"\babout\s+([A-Z][a-z]+)",
            r"\bsend\s+(?:a\s+)?(?:message\s+)?to\s+([A-Z][a-z]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1)
                if name.lower() not in {"me", "you", "us", "them", "his", "her", "a", "the"}:
                    return name

        return None

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract business entities from text:
        - Invoice IDs
        - Amounts
        - Dates
        - kVA sizes
        """
        entities = {}

        # Invoice IDs: INV-XXXX, #XXXX
        invoice_matches = re.findall(r"(?:INV[-#]?\s*|invoice\s*#?)\s*([A-Z0-9-]+)", text, re.IGNORECASE)
        if invoice_matches:
            entities["invoice_id"] = invoice_matches[0]

        # Amounts: Rs. XXXXX, ₹XXXXX
        amount_matches = re.findall(r"(?:Rs\.?|₹|INR)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if amount_matches:
            entities["amount"] = amount_matches[0].replace(",", "")

        # Dates
        date_matches = re.findall(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", text)
        if date_matches:
            entities["date"] = date_matches[0]

        # kVA sizes
        kva_matches = re.findall(r"(\d+)\s*(?:kva|kVA|KVA|kWp)", text, re.IGNORECASE)
        if kva_matches:
            entities["system_size_kva"] = int(kva_matches[0])

        return entities

    # --------------------------------------------------------------------------
    # ROUTING
    # --------------------------------------------------------------------------

    def route(self, text: str) -> WorkflowResult:
        """
        Parse intent from text and execute the appropriate workflow.

        This is the main entry point for processing Pravesh's Telegram messages.

        Args:
            text: Pravesh's message (voice note transcript or typed text)

        Returns:
            WorkflowResult from the executed workflow
        """
        intent_result = self.parse(text)

        logger.info(
            f"Routing: intent={intent_result.intent}, "
            f"customer={intent_result.customer_name}, "
            f"confidence={intent_result.confidence}"
        )

        # Dispatch to appropriate workflow
        if intent_result.intent == "send_whatsapp":
            customer = intent_result.customer_name or self._name_from_text(text)
            if not customer:
                return self._error_result("Could not find customer name in message")
            return send_support_message(
                customer_identifier=customer,
                message_text=intent_result.message_text or "",
            )

        elif intent_result.intent == "follow_up":
            customer = intent_result.customer_name
            if not customer:
                customer = self._name_from_text(text)
            if not customer:
                return self._error_result("Could not find customer name for follow-up")
            variable = customer
            return send_followup(customer_identifier=customer, variable=variable)

        elif intent_result.intent == "send_invoice":
            customer = intent_result.customer_name
            entities = self.extract_entities(text)
            return send_invoice(
                customer_identifier=customer or "UNKNOWN",
                invoice_id=entities.get("invoice_id", "INV-0001"),
                invoice_date=entities.get("date", "2024-01-01"),
                gst_details="GST details",
            )

        elif intent_result.intent == "send_proposal":
            return send_proposal(customer_identifier=intent_result.customer_name or "UNKNOWN")

        elif intent_result.intent == "price_quote":
            # Price quote → send follow-up asking for details
            customer = intent_result.customer_name or self._name_from_text(text)
            return send_followup(
                customer_identifier=customer or "Customer",
                variable="Customer",
            )

        elif intent_result.intent == "site_visit":
            customer = intent_result.customer_name or self._name_from_text(text)
            return send_followup(
                customer_identifier=customer or "Customer",
                variable="regarding site visit scheduling",
            )

        else:
            # General intent → smart send
            customer = intent_result.customer_name or self._name_from_text(text)
            if not customer:
                return self._error_result("Could not determine customer")
            return send_support_message(
                customer_identifier=customer,
                message_text=text,
            )

    def route_voice_transcript(self, transcript: str) -> WorkflowResult:
        """
        Route a voice note transcript the same way as typed text.

        Voice notes from Pravesh → STT → here → route()

        Args:
            transcript: The transcribed text from the voice note

        Returns:
            WorkflowResult from the executed workflow
        """
        logger.info(f"Routing voice transcript: '{transcript[:80]}...'")
        return self.route(transcript)

    # --------------------------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------------------------

    def _name_from_text(self, text: str) -> Optional[str]:
        """Extract customer name from text using patterns."""
        name = self._extract_name_fallback(text.lower())
        if name:
            try:
                self.resolver.search(name)
                return name
            except CustomerNotFoundError:
                pass
        return None

    def _error_result(self, error_message: str) -> WorkflowResult:
        """Create a failed WorkflowResult."""
        return WorkflowResult(
            success=False,
            method=None,
            template_name=None,
            message_id=None,
            phone="",
            customer_name=None,
            window_open=False,
            error=error_message,
            details={},
        )


# ==============================================================================
# CONVENIENCE FUNCTION
# ==============================================================================

_processor: Optional[WhatsAppProcessor] = None


def get_processor() -> WhatsAppProcessor:
    """Get or create the default processor."""
    global _processor
    if _processor is None:
        _processor = WhatsAppProcessor()
    return _processor


def process_message(text: str) -> WorkflowResult:
    """One-shot message processing."""
    return get_processor().route(text)


def process_voice_transcript(transcript: str) -> WorkflowResult:
    """One-shot voice transcript processing."""
    return get_processor().route_voice_transcript(transcript)


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "IntentResult",
    "WhatsAppProcessor",
    "get_processor",
    "process_message",
    "process_voice_transcript",
]