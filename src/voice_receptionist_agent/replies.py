"""Reply drafting. Every reply uses only business facts and caller details."""

from .models import BusinessProfile, Intent, Route


def greeting(business: BusinessProfile) -> str:
    return (
        f"Hello, thank you for calling {business.name}. "
        "This is our AI receptionist. How can I help you today?"
    )


def draft_reply(intent: str, route: str, details: dict, missing: list,
                caller_name: str | None, business: BusinessProfile) -> str:
    """Draft the receptionist reply for this call state."""
    name = f" {caller_name}" if caller_name else ""

    if route == Route.HUMAN:
        if intent == Intent.HUMAN and details.get("reason"):
            return (
                f"Of course{name}. I will connect you with a member of our team "
                f"about that. You can also reach us at {business.phone}."
            )
        return (
            f"Of course{name}. {business.handoff_message} "
            f"You can also reach us at {business.phone}."
        )

    if route == Route.CLARIFY:
        if "service" in missing and "day" in missing:
            return (
                f"Happy to help{name}. Which service would you like to book, "
                f"and which day works for you? Our services are "
                f"{', '.join(business.services)}."
            )
        if "service" in missing:
            return (
                f"Happy to help{name}. Which service is this about? "
                f"Our services are {', '.join(business.services)}."
            )
        if "day" in missing:
            service = details.get("service", "appointment")
            return (
                f"Happy to help{name}. Which day would you like to book "
                f"the {service} for? We are open {business.hours}."
            )
        return f"Happy to help{name}. Could you tell me a little more?"

    if route == Route.BOOK:
        service = details.get("service", "appointment")
        day = details.get("day", "")
        time = details.get("time", "")
        when = day + (" at " + time if time else "")
        return (
            f"Thank you{name}. I have noted a {service} booking for {when}. "
            "Our team will call you back shortly to confirm the slot. "
            "Is there anything else I can help with?"
        )

    if route == Route.ANSWER and intent == Intent.PRICING:
        service = details.get("service")
        if service:
            return (
                f"Thanks for asking{name}. {business.price_note} "
                f"Would you like to book the {service}?"
            )
        return f"Thanks for asking{name}. {business.price_note}"

    if route == Route.ANSWER and intent == Intent.HOURS:
        return (
            f"Thanks for asking{name}. We are open {business.hours}. "
            "Would you like to book an appointment?"
        )

    return (
        f"Thanks for calling{name}. {business.handoff_message} "
        f"You can also reach us at {business.phone}."
    )
