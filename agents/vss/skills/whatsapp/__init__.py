"""
WhatsApp Skills — VSustainAI Modular WhatsApp Framework
========================================================
Production-grade WhatsApp capabilities for VSustainAI.
Consumes shared STT infrastructure and DoubleTick API.

Architecture:
- client.py: Raw DoubleTick API (no business logic)
- templates.py: Template definitions and validation
- chat_window.py: 24-hour window logic
- contacts.py: Customer contact resolution (Google Contacts stub)
- formatter.py: Phone formatting and payload validation
- memory.py: CRM customer state and history
- workflows.py: High-level business flows
- processor.py: Intent routing for VSustainAI
- stt_integration.py: Voice note → WhatsApp pipeline
- config.py: Environment variable configuration
- exceptions.py: Custom exception hierarchy

Usage:
    # Simple send
    from skills.whatsapp.workflows import send_followup
    result = send_followup("Ramesh", variable="Ramesh")
    print(result.success, result.message_id)

    # Full pipeline with voice
    from skills.whatsapp.stt_integration import process_voice_for_whatsapp
    result = process_voice_for_whatsapp("/tmp/voice.ogg", customer_name="Ramesh")
    print(result["success"], result["text"], result["whatsapp_result"])

    # Process text command
    from skills.whatsapp.processor import process_message
    result = process_message("send a message to Ramesh about his pending payment")
    print(result.success, result.message_id)

Environment variables:
    DOUBLETICK_API_KEY — DoubleTick API key (required)
    WABA_NUMBER — Sender number (default: 919900108067)
    DOUBLETICK_BASE_URL — API base URL (default: https://public.doubletick.io)
    STT_API_URL — Shared STT endpoint (default: http://host.docker.internal:9001/transcribe)
    STT_API_FALLBACK — Fallback STT endpoint (default: http://localhost:9001/transcribe)
    REDIS_HOST — Redis host for CRM persistence (optional)
    REDIS_PORT — Redis port (default: 6379)
"""

from .config import (
    DOUBLETICK_API_KEY,
    WABA_NUMBER,
    DOUBLETICK_BASE_URL,
    STT_API_URL,
    STT_API_FALLBACK,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    DEFAULT_TIMEOUT_SECONDS,
    CHAT_WINDOW_TIMEOUT,
    validate_config,
)

from .exceptions import (
    WhatsAppError,
    ConfigError,
    MissingAPIKeyError,
    InvalidPhoneError,
    ChatWindowClosedError,
    TemplateValidationError,
    MediaValidationError,
    APIError,
    APITimeoutError,
    ChatWindowAPIError,
    CustomerNotFoundError,
    WorkflowError,
    CRMError,
)

from .formatter import (
    format_phone_number,
    validate_phone_number,
    strip_whatsapp_prefix,
    get_local_number,
    validate_placeholders,
    validate_media_url,
    generate_message_id,
    sanitize_text_for_whatsapp,
)

from .templates import (
    WhatsAppTemplate,
    TEMPLATES,
    get_template,
    list_templates,
    template_exists,
    validate_template_send,
    get_template_by_intent,
    build_placeholder_dict,
)

from .chat_window import (
    WindowStatus,
    ChatWindowChecker,
    get_checker,
    check_window,
    should_use_template,
    can_send_text,
)

from .client import (
    DoubleTickClient,
    get_client,
    send_template,
    send_text,
    check_chat_window,
)

from .memory import (
    LeadStage,
    MessageRecord,
    CustomerState,
    CustomerMemory,
    get_memory,
)

from .workflows import (
    WorkflowResult,
    WhatsAppWorkflow,
    send_followup,
    send_invoice,
    send_proposal,
    send_support_message,
)

from .processor import (
    IntentResult,
    WhatsAppProcessor,
    get_processor,
    process_message,
    process_voice_transcript,
)

from .stt_integration import (
    transcribe_audio,
    cleanup_temp_file,
    process_voice_for_whatsapp,
    transcribe_and_route,
)

__all__ = [
    # Config
    "DOUBLETICK_API_KEY",
    "WABA_NUMBER",
    "DOUBLETICK_BASE_URL",
    "STT_API_URL",
    "STT_API_FALLBACK",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_DB",
    "DEFAULT_TIMEOUT_SECONDS",
    "CHAT_WINDOW_TIMEOUT",
    "validate_config",
    # Exceptions
    "WhatsAppError",
    "ConfigError",
    "MissingAPIKeyError",
    "InvalidPhoneError",
    "ChatWindowClosedError",
    "TemplateValidationError",
    "MediaValidationError",
    "APIError",
    "APITimeoutError",
    "ChatWindowAPIError",
    "CustomerNotFoundError",
    "WorkflowError",
    "CRMError",
    # Formatter
    "format_phone_number",
    "validate_phone_number",
    "strip_whatsapp_prefix",
    "get_local_number",
    "validate_placeholders",
    "validate_media_url",
    "generate_message_id",
    "sanitize_text_for_whatsapp",
    # Templates
    "WhatsAppTemplate",
    "TEMPLATES",
    "get_template",
    "list_templates",
    "template_exists",
    "validate_template_send",
    "get_template_by_intent",
    "build_placeholder_dict",
    # Chat Window
    "WindowStatus",
    "ChatWindowChecker",
    "get_checker",
    "check_window",
    "should_use_template",
    "can_send_text",
    # Client
    "DoubleTickClient",
    "get_client",
    "send_template",
    "send_text",
    "check_chat_window",
    # Memory
    "LeadStage",
    "MessageRecord",
    "CustomerState",
    "CustomerMemory",
    "get_memory",
    # Workflows
    "WorkflowResult",
    "WhatsAppWorkflow",
    "send_followup",
    "send_invoice",
    "send_proposal",
    "send_support_message",
    # Processor
    "IntentResult",
    "WhatsAppProcessor",
    "get_processor",
    "process_message",
    "process_voice_transcript",
    # STT Integration
    "transcribe_audio",
    "cleanup_temp_file",
    "process_voice_for_whatsapp",
    "transcribe_and_route",
]

__version__ = "1.0.0"
__agent__ = "VSustainAI"