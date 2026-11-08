"""CLI: run a simulated call from typed caller lines.

Usage:
    python -m voice_receptionist_agent "Hi, my name is Ayesha, I want to book a cleaning on Saturday"
"""

import sys

from .graph import handle_call
from .models import BusinessProfile
from .router import route_summary


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("Usage: python -m voice_receptionist_agent \"<caller line>\" [\"<next line>\" ...]")
        return 1
    result = handle_call(argv, business=BusinessProfile())
    for line in result["transcript"]:
        print(f"{line['role'].title()}: {line['text']}")
    print(f"\nIntent: {result['intent']} | Route: {route_summary(result['route'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
