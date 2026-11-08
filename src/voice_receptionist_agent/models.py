"""Shared types for the voice receptionist agent."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypedDict


class Intent:
    BOOKING = "booking"
    PRICING = "pricing"
    HOURS = "hours"
    HUMAN = "human_handoff"
    OTHER = "other"

    ALL = (BOOKING, PRICING, HOURS, HUMAN, OTHER)


class Route:
    BOOK = "book"
    ANSWER = "answer"
    HUMAN = "human"
    CLARIFY = "clarify"


@dataclass
class BusinessProfile:
    """Facts the receptionist may state. Fill these in for your own business."""

    name: str = "Bright Smile Dental Clinic"
    services: List[str] = field(default_factory=lambda: ["checkup", "cleaning", "filling", "whitening"])
    hours: str = "Monday to Saturday, 9am to 6pm"
    price_note: str = "A checkup is 2,000 PKR and a cleaning is 3,500 PKR. Exact prices depend on the treatment."
    handoff_message: str = "I will connect you with a member of our team."
    phone: str = "+92 300 0000000"


class CallState(TypedDict, total=False):
    """State carried through the call flow graph."""

    caller_turns: List[str]
    caller_name: Optional[str]
    intent: str
    details: Dict[str, Any]
    missing: List[str]
    route: str
    reply: str
    transcript: List[Dict[str, str]]
    business: BusinessProfile
    llm_hook: Optional[Callable[[str], str]]
