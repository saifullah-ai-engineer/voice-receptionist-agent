"""Intent classification. Rule-based by default, optional LLM hook off by default."""

import re
from functools import lru_cache
from typing import Callable, Optional

from .models import BusinessProfile, Intent

_KEYWORDS = {
    Intent.BOOKING: [
        "book", "booking", "appointment", "schedule", "reserve", "slot",
        "available", "come in", "visit", "see the doctor", "checkup",
    ],
    Intent.PRICING: [
        "price", "cost", "how much", "charges", "fee", "fees", "rate",
        "package", "discount", "expensive", "pay",
    ],
    Intent.HOURS: [
        "hours", "open", "close", "closing", "timing", "timings",
        "when do you open", "what time", "working hours", "sunday",
    ],
    Intent.HUMAN: [
        "human", "person", "agent", "representative", "manager", "someone real",
        "talk to someone", "speak to someone", "real person", "staff",
        "complaint", "refund", "emergency",
    ],
}

_FILLER = ("please", "hi", "hello", "hey", "thanks", "thank you", "ok", "okay")


def classify_intent(text: str, llm_hook: Optional[Callable[[str], str]] = None) -> str:
    """Return one of the Intent values for the caller text.

    If an llm_hook is given it is tried first. Any failure or an
    unrecognised answer falls back to the rule-based classifier.
    """
    if llm_hook is not None:
        try:
            answer = llm_hook(text)
        except Exception:
            answer = None
        if isinstance(answer, str):
            cleaned = answer.strip().lower()
            if cleaned in Intent.ALL:
                return cleaned

    lowered = text.lower()
    scores = {intent: 0 for intent in Intent.ALL}
    for intent, words in _KEYWORDS.items():
        for word in words:
            if word in lowered:
                # Phrases like "how much" say more than a single word,
                # so they count double. This breaks ties like
                # "How much is a checkup?" (pricing) vs "checkup" (booking).
                scores[intent] += 2 if " " in word else 1

    best = max(scores, key=lambda key: scores[key])
    if scores[best] == 0:
        return Intent.OTHER
    return best


def extract_name(text: str) -> Optional[str]:
    """Pull a caller name out of phrases like 'my name is Ayesha'."""
    match = re.search(r"\b(?:my name is|this is|i am|i'm|call me)\s+([A-Za-z][A-Za-z' -]{1,30})", text, re.IGNORECASE)
    if not match:
        return None
    name = match.group(1).strip()
    name = re.split(r"\b(?:and|i|we|want|need|would|like|for|to)\b", name, flags=re.IGNORECASE)[0].strip(" ,.")
    return name.title() if name else None


def extract_details(text: str, intent: str, business: Optional[BusinessProfile] = None) -> dict:
    """Pull the facts each intent needs out of the caller text.

    Services are matched against the business profile, so an agency
    configuring a salon extracts "haircut" and a clinic extracts
    "cleaning". Without a business, the original dental service list
    is used so direct callers keep the old behaviour.
    """
    lowered = text.lower()
    details: dict = {}

    service_match = _service_pattern(
        tuple(business.services) if business is not None else None
    ).search(lowered)
    if service_match:
        details["service"] = _canonical_service(service_match.group(0), business)

    day_match = re.search(
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow)\b",
        lowered,
    )
    if day_match:
        details["day"] = day_match.group(1).title()

    time_match = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b", lowered)
    if time_match:
        details["time"] = time_match.group(1).replace(" ", "")

    if intent == Intent.HUMAN:
        reason = re.sub(r"\s+", " ", text).strip()
        details["reason"] = reason[:120]

    return details


def missing_details(intent: str, details: dict) -> list:
    """What the receptionist still needs before it can act on this intent."""
    needed = {
        Intent.BOOKING: ["service", "day"],
        Intent.PRICING: ["service"],
        Intent.HOURS: [],
        Intent.HUMAN: [],
        Intent.OTHER: [],
    }
    return [field for field in needed.get(intent, []) if field not in details]


def strip_filler(text: str) -> str:
    words = [w for w in text.split() if w.lower().strip(".,!?") not in _FILLER]
    return " ".join(words)


_LEGACY_SERVICES = (
    "checkup", "check-up", "cleaning", "filling", "whitening",
    "extraction", "braces", "consultation",
)


@lru_cache(maxsize=32)
def _service_pattern(services: Optional[tuple] = None):
    """Compiled service matcher for one business profile.

    Services are longest first so a multi-word service such as
    "root canal" matches before a shorter one. The pattern is cached
    per service list so repeated calls do not rebuild it.
    """
    if services is None:
        services = _LEGACY_SERVICES
    ordered = sorted(services, key=len, reverse=True)
    joined = "|".join(re.escape(service) for service in ordered)
    return re.compile(rf"(?<![A-Za-z])(?:{joined})(?![A-Za-z])", re.IGNORECASE)


def _canonical_service(matched: str, business: Optional[BusinessProfile]) -> str:
    """Return the service name exactly as the business lists it."""
    if business is None:
        return matched.lower().replace("check-up", "checkup")
    for service in business.services:
        if service.lower() == matched.lower():
            return service
    return matched.lower()
