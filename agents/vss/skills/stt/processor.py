"""
STT Processor — VSustainAI
============================
VSustainAI-specific voice processing for VSS business operations.

Responsibilities:
- Customer intent extraction from voice notes
- CRM-ready transcript formatting
- Sales/support workflow extraction
- WhatsApp voice handling
- Customer name/number extraction

This is VSustainAI-specific. For ROOTAI, use the separate
processor in /home/aiops/.openclaw/workspace/skills/stt/
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple

from .stt_client import transcribe_with_retry, validate_file, STT_API_URL
from .temp_audio_manager import TempAudioManager

logger = logging.getLogger(__name__)

VSUSTAINAI_STT_CONFIG = {
    "api_url": STT_API_URL,
    "timeout_seconds": 60,
    "max_retries": 2,
    "auto_cleanup": True,
    "supported_formats": ["ogg", "mp3", "wav", "m4a", "opus"],
}


class VSustainAI_STT_Processor:
    """
    VSustainAI STT processor — handles voice input for Pravesh + VSS customers.

    Workflow:
    1. Pravesh sends voice note via Telegram → VSustainAI
    2. Audio transcribed via shared STT API
    3. Intent extracted: customer name, action, context
    4. Formatted for CRM update or WhatsApp action
    5. Temp files auto-deleted
    """

    def __init__(
        self,
        temp_manager: Optional[TempAudioManager] = None,
        auto_cleanup: bool = True,
    ):
        self.temp_manager = temp_manager or TempAudioManager()
        self.auto_cleanup = auto_cleanup

    def process_voice_note(
        self,
        file_path: str,
        inject_context: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a voice note and extract VSS business context.

        Returns:
            {
                "success": bool,
                "text": str,                # raw transcript
                "summary": str,             # one-line summary
                "customer_name": str,       # extracted customer name
                "intent": str,              # send_message, update_crm, etc.
                "entities": dict,           # extracted entities (phone, amount, etc.)
                "crm_ready": bool,         # can this be directly written to CRM?
                "whatsapp_action": dict,   # WhatsApp action to take
                "language": str,
                "error": str or None,
                "metadata": dict,
            }
        """
        result = self._default_result()

        validation = validate_file(file_path)
        if not validation["valid"]:
            result["error"] = validation["error"]
            return result

        try:
            logger.info(f"VSustainAI STT: transcribing {file_path}")
            stt_result = transcribe_with_retry(
                file_path,
                timeout_seconds=VSUSTAINAI_STT_CONFIG["timeout_seconds"],
                max_retries=VSUSTAINAI_STT_CONFIG["max_retries"],
            )

            if not stt_result["success"]:
                result["error"] = stt_result["error"]
                return result

            transcript = stt_result["text"]
            language = stt_result["language"]

            # Extract business entities
            customer_name = self._extract_customer_name(transcript)
            intent = self._extract_intent(transcript)
            entities = self._extract_entities(transcript)
            whatsapp_action = self._build_whatsapp_action(transcript, intent, customer_name)

            result = {
                "success": True,
                "text": transcript,
                "summary": self._generate_summary(transcript),
                "customer_name": customer_name,
                "intent": intent,
                "entities": entities,
                "crm_ready": self._is_crm_ready(intent, entities),
                "whatsapp_action": whatsapp_action,
                "language": language,
                "error": None,
                "metadata": {
                    "file_size_mb": stt_result["metadata"].get("file_size_mb", 0),
                    "retries": stt_result["metadata"].get("retries", 0),
                    "agent": "VSustainAI",
                    "business_context": "VSS_solar_operations",
                },
            }

            logger.info(f"VSustainAI STT success: intent={intent}, customer={customer_name}")

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            logger.error(f"VSustainAI STT failure: {e}")

        finally:
            if self.auto_cleanup:
                self.temp_manager.cleanup(file_path)

        return result

    def process_telegram_voice(
        self,
        telegram_file_path: str,
        save_to_temp: bool = True,
    ) -> Dict[str, Any]:
        """
        Process voice note from Pravesh via Telegram.
        """
        input_path = telegram_file_path

        if save_to_temp:
            input_path = self.temp_manager.save_temp_from_existing(
                telegram_file_path, copy=True
            )

        return self.process_voice_note(input_path, inject_context=True)

    def _default_result(self) -> Dict[str, Any]:
        return {
            "success": False,
            "text": "",
            "summary": "",
            "customer_name": "",
            "intent": "unknown",
            "entities": {},
            "crm_ready": False,
            "whatsapp_action": {},
            "language": "unknown",
            "error": None,
            "metadata": {"agent": "VSustainAI"},
        }

    def _extract_customer_name(self, transcript: str) -> str:
        """
        Extract customer name from transcript.
        Looks for patterns like "send to Ramesh", "update Amit", etc.
        """
        patterns = [
            r"to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",  # "to Ramesh", "to Ramesh Kumar"
            r"for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", # "for Ramesh"
            r"about\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", # "about Ramesh"
            r"tell\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",  # "tell Ramesh"
            r"message\s+([A-Z][a-z]+)",                  # "message Ramesh"
            r"contact\s+([A-Z][a-z]+)",                   # "contact Ramesh"
        ]

        for pattern in patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common non-names
                if name.lower() not in {"me", "you", "us", "them", "him", "her", "a", "the"}:
                    return name

        return ""

    def _extract_intent(self, transcript: str) -> str:
        """
        Classify voice note intent for VSS workflows.
        """
        transcript_lower = transcript.lower()

        intent_patterns = {
            "send_whatsapp": [
                r"send\s+.*whatsapp",
                r"send\s+.*message",
                r"whatsapp\s+.*to",
                r"text\s+.*to",
                r"message\s+.*about",
            ],
            "update_crm": [
                r"update\s+.*crm",
                r"add\s+.*to\s+.*crm",
                r"put\s+.*in\s+.*crm",
                r"record\s+.*in\s+.*crm",
                r"log\s+.*in\s+.*crm",
            ],
            "follow_up": [
                r"follow\s+up",
                r"chasing",
                r"pending",
                r"remind",
                r"check\s+on",
            ],
            "price_quote": [
                r"price\s+quote",
                r"quote\s+for",
                r"how\s+much",
                r"cost\s+of",
                r"price\s+for",
                r"system\s+price",
                r"kva\s+price",
            ],
            "site_visit": [
                r"site\s+visit",
                r"visit\s+the\s+site",
                r"schedule\s+visit",
                r"installation",
            ],
            "payment": [
                r"payment",
                r"pay\s+.*amount",
                r"invoice",
                r"due\s+.*payment",
                r"collection",
            ],
            "complaint": [
                r"issue",
                r"problem",
                r"not\s+working",
                r"complaint",
                r"defect",
            ],
            "inquiry": [
                r"interested",
                r"enquiry",
                r"want\s+to\s+know",
                r"information\s+about",
                r"do\s+you\s+have",
            ],
        }

        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, transcript_lower):
                    return intent

        return "general"

    def _extract_entities(self, transcript: str) -> Dict[str, Any]:
        """
        Extract business entities: phone numbers, system sizes, amounts, dates.
        """
        entities = {}

        # Phone numbers
        phone_pattern = r"(?:91|\+91)?\s*([6-9]\d{9})"
        phone_matches = re.findall(phone_pattern, transcript.replace(" ", ""))
        if phone_matches:
            phones = [f"91{p}"[-12:] for p in phone_matches]
            entities["phone_numbers"] = phones

        # System sizes (kVA)
        kva_pattern = r"(\d+)\s*(?:kva|kVA|KVA|kWp|kWP|kva\s+system)"
        kva_matches = re.findall(kva_pattern, transcript, re.IGNORECASE)
        if kva_matches:
            entities["system_sizes_kva"] = [int(k) for k in kva_matches]

        # Amounts
        amount_pattern = r"(?:rs\.?|₹|INR)\s*([\d,]+(?:\.\d{2})?)"
        amount_matches = re.findall(amount_pattern, transcript, re.IGNORECASE)
        if amount_matches:
            entities["amounts"] = [a.replace(",", "") for a in amount_matches]

        # Dates
        date_patterns = [
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})",
        ]
        for dp in date_patterns:
            date_match = re.search(dp, transcript, re.IGNORECASE)
            if date_match:
                entities["date_mentioned"] = date_match.group(1)
                break

        return entities

    def _is_crm_ready(self, intent: str, entities: Dict) -> bool:
        """Check if we have enough to write to CRM directly."""
        if intent in ("send_whatsapp", "inquiry", "follow_up"):
            return bool(entities.get("phone_numbers") or entities.get("customer_name"))
        if intent == "price_quote":
            return bool(entities.get("system_sizes_kva"))
        return False

    def _build_whatsapp_action(
        self, transcript: str, intent: str, customer_name: str
    ) -> Dict[str, Any]:
        """
        Build a WhatsApp action object based on transcript.
        """
        action = {
            "intent": intent,
            "template": None,
            "variables": [],
            "free_text": None,
            "send": False,
        }

        if intent == "send_whatsapp":
            # Default to chat_support template
            action["template"] = "chat_support"
            action["variables"] = [customer_name] if customer_name else ["Customer"]
            action["send"] = True

        elif intent == "price_quote":
            # Extract system size for context
            kva_match = re.search(r"(\d+)\s*(?:kva|kVA)", transcript, re.IGNORECASE)
            if kva_match:
                action["free_text"] = f"Hi {customer_name}, regarding the {kva_match.group(1)}kVA system you inquired about"
            else:
                action["free_text"] = f"Hi {customer_name}, regarding your solar inquiry"
            action["send"] = True

        elif intent == "follow_up":
            action["template"] = "chat_support"
            action["variables"] = [customer_name] if customer_name else ["Customer"]
            action["send"] = True

        return action

    def _generate_summary(self, transcript: str, max_length: int = 100) -> str:
        if not transcript:
            return ""
        transcript = transcript.strip()
        if len(transcript) <= max_length:
            return transcript
        truncated = transcript[:max_length]
        last_space = truncated.rfind(" ")
        last_period = truncated.rfind(".")
        breakpoint = max(last_space, last_period)
        if breakpoint > max_length * 0.5:
            return transcript[: breakpoint + 1]
        return truncated + "..."

    def batch_process(self, file_paths: List[str]) -> Dict[str, Any]:
        results = []
        successful = 0
        failed = 0

        for path in file_paths:
            result = self.process_voice_note(path)
            results.append(result)
            if result["success"]:
                successful += 1
            else:
                failed += 1

        return {
            "total": len(file_paths),
            "successful": successful,
            "failed": failed,
            "results": results,
        }


def process_voice_input(file_path: str, agent_type: str = "VSustainAI") -> Dict[str, Any]:
    """
    Convenience function for one-shot voice processing.
    """
    if agent_type == "VSustainAI":
        processor = VSustainAI_STT_Processor()
        return processor.process_voice_note(file_path)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")