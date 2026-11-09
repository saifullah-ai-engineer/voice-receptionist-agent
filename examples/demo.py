"""Demo: three simulated calls through the voice receptionist agent.

Run: PYTHONPATH=src .venv/bin/python examples/demo.py
No paid API, no phone line, no voice service. Text only.

Use --config to run the demo for a different business:
    PYTHONPATH=src .venv/bin/python examples/demo.py --config business.json

Use --speak to also render each reply as spoken audio. That needs a
voice reference and the voice-clone-pipeline synthesize script:
    PYTHONPATH=src .venv/bin/python examples/demo.py --speak \
        --voice-ref ~/workspace/voice-library/my_voice.wav \
        --synth-script ~/workspace/voice-library/synthesize.sh
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from voice_receptionist_agent.config import resolve_business_profile
from voice_receptionist_agent.graph import handle_call
from voice_receptionist_agent.router import route_summary
from voice_receptionist_agent.voice import speak

CALLS = [
    ("Call 1: booking", ["Hi, my name is Ayesha, I want to book a cleaning on Saturday at 10am"]),
    ("Call 2: price question", ["Hello, how much does a checkup cost?"]),
    ("Call 3: human handoff", ["I need to speak to a real person about a refund, please"]),
]


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Voice receptionist demo.")
    parser.add_argument("--config", default=None,
                        help="Path to a business.json config file.")
    parser.add_argument("--speak", action="store_true",
                        help="Also render each reply as spoken audio.")
    parser.add_argument("--voice-ref", default=None,
                        help="Voice reference audio, 5 to 20 seconds, wav.")
    parser.add_argument("--synth-script", default=None,
                        help="Voice-clone-pipeline synthesize script.")
    args = parser.parse_args(argv)
    try:
        business = resolve_business_profile(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    voice_ref = args.voice_ref or os.environ.get("VRA_VOICE_REF")
    synth_script = args.synth_script or os.environ.get("VRA_SYNTH_SCRIPT")
    if args.speak and (not voice_ref or not synth_script):
        print(
            "Voice error: --speak needs a voice reference audio and a "
            "synthesize script. Pass --voice-ref and --synth-script, or "
            "set VRA_VOICE_REF and VRA_SYNTH_SCRIPT.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    print(f"Business: {business.name}")
    for title, turns in CALLS:
        print("=" * 60)
        print(title)
        print("=" * 60)
        result = handle_call(turns, business=business)
        for line in result["transcript"]:
            print(f"{line['role'].title()}: {line['text']}")
        print(f"\nOutcome: intent={result['intent']}, route={route_summary(result['route'])}")
        try:
            saved = speak(
                result["reply"],
                "reply.txt",
                voice_ref=voice_ref if args.speak else None,
                synthesize_script=synth_script if args.speak else None,
            )
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            print(f"Voice error: {exc}", file=sys.stderr)
            raise SystemExit(2)
        if args.speak:
            print(f"Reply spoken as audio: {saved}")
        else:
            print("Reply also saved to reply.txt for a voice service to speak.")
        print()


if __name__ == "__main__":
    main()
