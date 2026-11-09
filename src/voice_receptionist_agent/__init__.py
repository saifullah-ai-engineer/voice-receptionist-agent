"""voice-receptionist-agent: a voice receptionist for small businesses."""

from .config import load_business_profile, resolve_business_profile
from .models import BusinessProfile, Intent, Route

__all__ = [
    "build_graph",
    "handle_call",
    "load_business_profile",
    "resolve_business_profile",
    "BusinessProfile",
    "Intent",
    "Route",
]
__version__ = "0.2.2"


def __getattr__(name):
    """Load the graph lazily so importing the package does not import langgraph."""
    if name in {"build_graph", "handle_call"}:
        from .graph import build_graph, handle_call

        globals()[name] = build_graph if name == "build_graph" else handle_call
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
