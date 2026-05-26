"""
Contacts — Customer Contact Resolution
=======================================
Handles Google Contacts lookup for customer phone number resolution.
Receives a customer name → returns phone number.

Usage:
    from skills.whatsapp.contacts import ContactResolver, search_contact

    resolver = ContactResolver()
    contact = resolver.search("Ramesh")
    print(contact.phone)  # "919876543210"
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .formatter import format_phone_number
from .exceptions import CustomerNotFoundError

logger = logging.getLogger(__name__)

# ==============================================================================
# CONTACT DATACLASS
# ==============================================================================

@dataclass
class Contact:
    """
    A customer contact.
    """
    name: str
    phone: str  # Already formatted as 91XXXXXXXXXX
    phone_local: str  # 10-digit local number
    display_name: str
    lookup_key: str  # How this was found (name, phone, email, etc.)
    raw: Optional[dict] = None  # Raw API response if available

    def __post_init__(self):
        # Normalize phone on creation
        self.phone = format_phone_number(self.phone)
        self.phone_local = self.phone[2:]  # Strip 91

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "phone": self.phone,
            "display_name": self.display_name,
            "lookup_key": self.lookup_key,
        }


# ==============================================================================
# CONTACT RESOLVER
# ==============================================================================

class ContactResolver:
    """
    Resolves customer names/identifiers to Contact objects with phone numbers.

    This is a wrapper around Google Contacts API.
    Currently uses a STUB implementation — replace with real Google Contacts integration.

    The interface is designed so the real implementation can drop in
    without changing any calling code.
    """

    def __init__(self, access_token: Optional[str] = None):
        """
        Args:
            access_token: Google OAuth access token for Contacts API.
                          If None, will attempt to use stored refresh token.
        """
        self.access_token = access_token

    def search(self, identifier: str) -> Optional[Contact]:
        """
        Search for a contact by name, phone, or any identifier.

        Args:
            identifier: Customer name ("Ramesh"), phone, or email

        Returns:
            Contact object if found, None if not found

        Raises:
            CustomerNotFoundError: If contact cannot be found
        """
        # Normalize identifier
        identifier = identifier.strip()

        if not identifier:
            raise CustomerNotFoundError("(empty identifier)")

        # Try as phone number first
        try:
            formatted = format_phone_number(identifier)
            contact = self._search_by_phone(formatted)
            if contact:
                logger.info(f"Contact found by phone: {identifier} → {formatted}")
                return contact
        except ValueError:
            pass  # Not a phone number, try as name

        # Try as name search
        contact = self._search_by_name(identifier)
        if contact:
            logger.info(f"Contact found by name: {identifier}")
            return contact

        # Not found
        raise CustomerNotFoundError(identifier)

    def _search_by_phone(self, phone: str) -> Optional[Contact]:
        """
        Search for contact by phone number.
        STUB — replace with actual Google Contacts API call.
        """
        # TODO: Implement real Google Contacts lookup
        # Currently returns None (not found) for all phone searches
        #
        # Real implementation would:
        # GET https://people.googleapis.com/v1/people:searchContacts
        # Query: {"query": phone, "readMask": "names,phoneNumbers"}
        return None

    def _search_by_name(self, name: str) -> Optional[Contact]:
        """
        Search for contact by name.
        STUB — replace with actual Google Contacts API call.

        For now, returns a hardcoded stub contact so the WhatsApp
        workflow can be tested without a live Google Contacts connection.
        """
        # TODO: Implement real Google Contacts lookup
        #
        # Real implementation would:
        # GET https://people.googleapis.com/v1/people:searchContacts
        # Query: {"query": name, "readMask": "names,phoneNumbers"}

        # STUB DATABASE — for testing without live Google Contacts
        # Remove this when real Google Contacts integration is added
        stub_contacts = {
            "ramesh": Contact(
                name="Ramesh",
                phone="919876543210",
                phone_local="9876543210",
                display_name="Ramesh Kumar",
                lookup_key="name:ramesh",
            ),
            "amit": Contact(
                name="Amit",
                phone="919988776655",
                phone_local="9988776655",
                display_name="Amit Sharma",
                lookup_key="name:amit",
            ),
            "priya": Contact(
                name="Priya",
                phone="919922113344",
                phone_local="9922113344",
                display_name="Priya Patel",
                lookup_key="name:priya",
            ),
        }

        name_lower = name.lower().strip()
        contact = stub_contacts.get(name_lower)

        if contact:
            logger.warning(
                f"[STUB] Contact lookup for '{name}' returned stub contact. "
                f"Replace with real Google Contacts API before production."
            )

        return contact

    def get_or_create(self, identifier: str) -> Contact:
        """
        Get contact or raise CustomerNotFoundError.

        Alias of search() for semantic clarity in workflow code.
        """
        return self.search(identifier)

    def resolve_to_phone(self, identifier: str) -> str:
        """
        Given a name or phone identifier, return formatted phone number.

        Args:
            identifier: Name or phone

        Returns:
            Phone in 91XXXXXXXXXX format

        Raises:
            CustomerNotFoundError: If not found
        """
        contact = self.search(identifier)
        return contact.phone


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

_resolver: Optional[ContactResolver] = None


def get_resolver() -> ContactResolver:
    """Get or create the default ContactResolver."""
    global _resolver
    if _resolver is None:
        _resolver = ContactResolver()
    return _resolver


def search_contact(name_or_phone: str) -> Optional[Contact]:
    """
    One-shot contact search using default resolver.
    Returns None if not found.
    """
    try:
        return get_resolver().search(name_or_phone)
    except CustomerNotFoundError:
        return None


def resolve_phone(identifier: str) -> str:
    """
    One-shot: given a name, return phone number.

    Raises CustomerNotFoundError if not found.
    """
    return get_resolver().resolve_to_phone(identifier)


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "Contact",
    "ContactResolver",
    "get_resolver",
    "search_contact",
    "resolve_phone",
    "CustomerNotFoundError",
]