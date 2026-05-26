"""
Memory — CRM Customer Interaction Memory
=========================================
Stores customer interaction history and lead state.
Supports both in-memory (default) and Redis (for scalability).

Stores:
- customer name, phone, last contact time
- last message sent/received
- chat window state (last known)
- lead stage (inquiry, qualified, proposal, closed)
- pending actions
- transcript history (last N voice notes)

Usage:
    from skills.whatsapp.memory import CustomerMemory, get_memory

    memory = get_memory()
    memory.record_outbound("919876543210", "chat_support", ["Ramesh"], message_id="abc123")
    state = memory.get_customer_state("919876543210")
    print(state.lead_stage)  # "inquiry"
"""

import json
import logging
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

# ==============================================================================
# LEAD STAGES
# ==============================================================================

class LeadStage(str, Enum):
    """Customer lead stage in the sales pipeline."""
    NEW = "new"                     # First contact
    INQUIRY = "inquiry"             # Initial inquiry received
    QUALIFIED = "qualified"         # Lead qualified as real opportunity
    PROPOSAL = "proposal"           # Proposal/quote sent
    NEGOTIATION = "negotiation"     # In price discussion
    CLOSED_WON = "closed_won"       # Deal won
    CLOSED_LOST = "closed_lost"     # Deal lost
    ON_HOLD = "on_hold"            # Paused/deprioritized


# ==============================================================================
# MESSAGE RECORD
# ==============================================================================

@dataclass
class MessageRecord:
    """A single outbound message record."""
    timestamp: str          # ISO 8601
    direction: str          # "outbound" or "inbound"
    method: str             # "template" or "text"
    template_name: Optional[str]
    content: str            # Preview of message content
    message_id: str         # DoubleTick message ID
    success: bool

    def to_dict(self) -> dict:
        return asdict(self)


# ==============================================================================
# CUSTOMER STATE
# ==============================================================================

@dataclass
class CustomerState:
    """
    Full state for a single customer.
    """
    phone: str
    name: Optional[str] = None
    last_contact: Optional[str] = None       # ISO timestamp
    last_message_preview: Optional[str] = None
    window_open: bool = False
    last_window_check: Optional[str] = None   # ISO timestamp
    lead_stage: str = LeadStage.NEW.value
    pending_actions: List[str] = []            # e.g., ["send_quote", "follow_up"]
    message_history: List[MessageRecord] = []  # Last N messages
    tags: List[str] = []                       # e.g., ["solar_inquiry", "bangalore"]
    notes: str = ""                            # Free-form notes

    def to_dict(self) -> dict:
        d = asdict(self)
        d["message_history"] = [m.to_dict() if isinstance(m, MessageRecord) else m for m in d["message_history"]]
        return d

    @classmethod
    def from_dict(cls, d: dict) "CustomerState":
        d = dict(d)  # copy
        if "message_history" in d:
            d["message_history"] = [MessageRecord(**m) if isinstance(m, dict) else m for m in d["message_history"]]
        return cls(**d)

    def update_window_status(self, window_open: bool) -> None:
        """Update cached chat window status."""
        self.window_open = window_open
        self.last_window_check = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def add_message(self, record: MessageRecord) -> None:
        """Append a message record, trim history to last 50."""
        self.message_history.append(record)
        if len(self.message_history) > 50:
            self.message_history = self.message_history[-50:]

    def advance_stage(self, new_stage: str) -> None:
        """Move lead to new stage."""
        old = self.lead_stage
        self.lead_stage = new_stage
        logger.info(f"Customer {self.phone}: lead stage {old} → {new_stage}")

    def add_pending_action(self, action: str) -> None:
        """Add a pending action if not already present."""
        if action not in self.pending_actions:
            self.pending_actions.append(action)

    def complete_action(self, action: str) -> None:
        """Remove a completed pending action."""
        if action in self.pending_actions:
            self.pending_actions.remove(action)

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        if tag in self.tags:
            self.tags.remove(tag)


# ==============================================================================
# MEMORY STORE
# ==============================================================================

class CustomerMemory:
    """
    In-memory CRM customer state store with Redis persistence option.

    For production at scale, set REDIS_HOST in config.
    Falls back to in-memory dict when Redis is unavailable.
    """

    MAX_HISTORY = 50  # Max messages per customer

    def __init__(
        self,
        redis_host: Optional[str] = None,
        redis_port: int = 6379,
        redis_db: int = 0,
        use_redis: bool = True,
    ):
        """
        Args:
            redis_host: Redis host for persistence (None = in-memory only)
            redis_port: Redis port
            redis_db: Redis database number
            use_redis: If True, try Redis; if False, force in-memory
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self._redis_client = None
        self._memory: Dict[str, CustomerState] = {}  # phone → state
        self._redis_available = False

        if use_redis and redis_host:
            self._connect_redis()

    def _connect_redis(self) -> None:
        """Attempt to connect to Redis."""
        try:
            import redis
            self._redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            # Test connection
            self._redis_client.ping()
            self._redis_available = True
            logger.info(f"CustomerMemory connected to Redis at {self.redis_host}:{self.redis_port}")
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}), falling back to in-memory")
            self._redis_client = None
            self._redis_available = False

    def _redis_key(self, phone: str) -> str:
        """Redis key for a customer."""
        return f"crm:customer:{phone}"

    # --------------------------------------------------------------------------
    # CORE CRUD
    # --------------------------------------------------------------------------

    def get_customer_state(self, phone: str) -> Optional[CustomerState]:
        """
        Get full state for a customer.

        Returns None if customer not in memory.
        """
        formatted = None
        try:
            from .formatter import format_phone_number
            formatted = format_phone_number(phone)
        except ValueError:
            return None

        # Try Redis first
        if self._redis_available and self._redis_client:
            key = self._redis_key(formatted)
            data = self._redis_client.get(key)
            if data:
                try:
                    d = json.loads(data)
                    return CustomerState.from_dict(d)
                except Exception:
                    pass  # Fall through to memory

        # Fall back to in-memory
        return self._memory.get(formatted)

    def upsert(self, state: CustomerState) -> None:
        """Create or update customer state."""
        # Persist to Redis
        if self._redis_available and self._redis_client:
            key = self._redis_key(state.phone)
            data = json.dumps(state.to_dict())
            # Expire in 90 days
            self._redis_client.setex(key, 90 * 24 * 3600, data)

        # Also keep in-memory copy
        self._memory[state.phone] = state

    def get_or_create(self, phone: str, name: str = None) -> CustomerState:
        """Get existing state or create new customer record."""
        state = self.get_customer_state(phone)
        if state:
            if name and not state.name:
                state.name = name
                self.upsert(state)
            return state

        # Create new
        formatted = None
        try:
            from .formatter import format_phone_number
            formatted = format_phone_number(phone)
        except ValueError:
            formatted = f"91{phone}"  # Best effort

        state = CustomerState(phone=formatted, name=name)
        self.upsert(state)
        return state

    def delete(self, phone: str) -> bool:
        """Delete customer record. Returns True if found and deleted."""
        formatted = None
        try:
            from .formatter import format_phone_number
            formatted = format_phone_number(phone)
        except ValueError:
            return False

        if self._redis_available and self._redis_client:
            self._redis_client.delete(self._redis_key(formatted))

        if formatted in self._memory:
            del self._memory[formatted]
            return True
        return False

    # --------------------------------------------------------------------------
    # BUSINESS OPERATIONS
    # --------------------------------------------------------------------------

    def record_outbound(
        self,
        phone: str,
        method: str,  # "template" or "text"
        placeholders: List[str] = None,
        template_name: str = None,
        message_id: str = None,
        content_preview: str = "",
        success: bool = True,
        name: str = None,
    ) -> CustomerState:
        """
        Record an outbound message sent to customer.

        This is called after every outbound WhatsApp send.
        """
        state = self.get_or_create(phone, name=name)

        # Update last contact
        state.last_contact = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        state.last_message_preview = content_preview[:100]

        # Add message record
        record = MessageRecord(
            timestamp=state.last_contact,
            direction="outbound",
            method=method,
            template_name=template_name,
            content=content_preview,
            message_id=message_id or "",
            success=success,
        )
        state.add_message(record)

        # Auto-advance stage if first contact
        if state.lead_stage == LeadStage.NEW.value:
            state.advance_stage(LeadStage.INQUIRY.value)

        self.upsert(state)
        return state

    def record_inbound(
        self,
        phone: str,
        content_preview: str = "",
        name: str = None,
    ) -> CustomerState:
        """
        Record an inbound customer reply.

        Called when a customer replies to a message.
        This resets the chat window.
        """
        state = self.get_or_create(phone, name=name)

        state.last_contact = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        state.last_message_preview = content_preview[:100]
        state.window_open = True  # Customer replied

        record = MessageRecord(
            timestamp=state.last_contact,
            direction="inbound",
            method="text",
            template_name=None,
            content=content_preview[:100],
            message_id="",
            success=True,
        )
        state.add_message(record)

        self.upsert(state)
        return state

    def get_pending_actions(self, phone: str) -> List[str]:
        """Get pending actions for a customer."""
        state = self.get_customer_state(phone)
        return list(state.pending_actions) if state else []

    def get_all_with_pending(self, action: str) -> List[CustomerState]:
        """Get all customers with a specific pending action."""
        results = []
        # Try Redis SCAN
        if self._redis_available and self._redis_client:
            try:
                cursor = 0
                while True:
                    cursor, keys = self._redis_client.scan(cursor, match="crm:customer:*", count=100)
                    for key in keys:
                        data = self._redis_client.get(key)
                        if data:
                            d = json.loads(data)
                            state = CustomerState.from_dict(d)
                            if action in state.pending_actions:
                                results.append(state)
                    if cursor == 0:
                        break
            except Exception:
                pass  # Fall through to in-memory

        # Also check in-memory
        for state in self._memory.values():
            if action in state.pending_actions and state not in results:
                results.append(state)

        return results

    def list_all(self, limit: int = 100) -> List[CustomerState]:
        """List all customers (limited)."""
        results = []

        if self._redis_available and self._redis_client:
            try:
                cursor = 0
                while len(results) < limit:
                    cursor, keys = self._redis_client.scan(cursor, match="crm:customer:*", count=50)
                    for key in keys:
                        data = self._redis_client.get(key)
                        if data:
                            results.append(CustomerState.from_dict(json.loads(data)))
                    if cursor == 0:
                        break
            except Exception:
                pass

        # Add any in-memory-only records
        for state in self._memory.values():
            if state not in results:
                results.append(state)
                if len(results) >= limit:
                    break

        # Sort by last_contact desc
        results.sort(key=lambda s: s.last_contact or "", reverse=True)
        return results[:limit]


# ==============================================================================
# GLOBAL INSTANCE
# ==============================================================================

_memory: Optional[CustomerMemory] = None


def get_memory(
    redis_host: str = None,
    redis_port: int = 6379,
    redis_db: int = 0,
) -> CustomerMemory:
    """Get or create the global CustomerMemory instance."""
    global _memory
    if _memory is None:
        from .config import REDIS_HOST
        _memory = CustomerMemory(
            redis_host=redis_host or REDIS_HOST,
            redis_port=redis_port,
            redis_db=redis_db,
        )
    return _memory


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "LeadStage",
    "MessageRecord",
    "CustomerState",
    "CustomerMemory",
    "get_memory",
]