"""Routing: decide what the call needs next, based on intent and details."""

from .models import Intent, Route


def route_for(intent: str, missing: list) -> str:
    """Return the route for this call."""
    if intent == Intent.HUMAN:
        return Route.HUMAN
    if missing:
        return Route.CLARIFY
    if intent == Intent.BOOKING:
        return Route.BOOK
    if intent in (Intent.PRICING, Intent.HOURS):
        return Route.ANSWER
    return Route.HUMAN


def route_summary(route: str) -> str:
    """A plain language description of the route, for the call log."""
    return {
        Route.BOOK: "Booking request, ready to confirm a slot",
        Route.ANSWER: "Question answered from business facts",
        Route.HUMAN: "Handed off to a human team member",
        Route.CLARIFY: "Waiting on missing details from the caller",
    }[route]
