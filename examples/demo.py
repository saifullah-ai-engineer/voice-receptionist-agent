"""Demo: three simulated calls through the voice receptionist agent.

Run: PYTHONPATH=src .venv/bin/python examples/demo.py
No paid API, no phone line, no voice service. Text only.
"""

from voice_receptionist_agent.graph import handle_call
from voice_receptionist_agent.models import BusinessProfile
from voice_receptionist_agent.router import route_summary
from voice_receptionist_agent.voice import speak

CALLS = [
    ("Call 1: booking", ["Hi, my name is Ayesha, I want to book a cleaning on Saturday at 10am"]),
    ("Call 2: price question", ["Hello, how much does a checkup cost?"]),
    ("Call 3: human handoff", ["I need to speak to a real person about a refund, please"]),
]


def main() -> None:
    business = BusinessProfile()
    for title, turns in CALLS:
        print("=" * 60)
        print(title)
        print("=" * 60)
        result = handle_call(turns, business=business)
        for line in result["transcript"]:
            print(f"{line['role'].title()}: {line['text']}")
        print(f"\nOutcome: intent={result['intent']}, route={route_summary(result['route'])}")
        speak(result["reply"], "reply.txt")
        print("Reply also saved to reply.txt for a voice service to speak.")
        print()


if __name__ == "__main__":
    main()
