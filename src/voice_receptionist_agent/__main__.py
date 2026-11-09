"""CLI: run a simulated call from typed caller lines.

Usage:
    python -m voice_receptionist_agent "Hi, my name is Ayesha, I want to book a cleaning on Saturday"
    python -m voice_receptionist_agent --config business.json "How much is a cleaning?"
    python -m voice_receptionist_agent --speak "Hello, how much is a checkup?"

With no --config, a business.json in the current directory is used
when it exists. Otherwise the built-in example business is used.

With --speak, the reply is also rendered as audio in the business
voice. The voice reference and synthesize script come from
--voice-ref and --synth-script, or from the VRA_VOICE_REF and
VRA_SYNTH_SCRIPT environment variables. Without them, the reply
stays as text.

With --quiet, the caller transcript is not printed, only the outcome.
Use it when the console output is logged, so caller words do not end
up in a log file.

When VRA_API_TOKEN is set, the CLI also needs --token with the same
value. The token is off unless the operator sets it.
"""

import argparse
import os
import sys

from . import __version__
from .config import resolve_business_profile
from .graph import handle_call
from .router import route_summary
from .security import check_cli_token
from .voice import speak


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="voice-receptionist-agent",
        description="Run a simulated call through the voice receptionist agent.",
    )
    parser.add_argument("caller", nargs="*", help="Caller lines, in order.")
    parser.add_argument("--config", default=None,
                        help="Path to a business.json config file.")
    parser.add_argument("--out", default="reply.txt",
                        help="File the reply text is saved to.")
    parser.add_argument("--speak", action="store_true",
                        help="Also render the reply as spoken audio.")
    parser.add_argument("--voice-ref", default=None,
                        help="Voice reference audio, 5 to 20 seconds, wav.")
    parser.add_argument("--synth-script", default=None,
                        help="Voice-clone-pipeline synthesize script.")
    parser.add_argument("--token", default=None,
                        help="CLI token, only needed when VRA_API_TOKEN is set.")
    parser.add_argument("--quiet", action="store_true",
                        help="Do not print the caller transcript, only the outcome.")
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.caller:
        parser.print_usage(sys.stderr)
        print("Give at least one caller line in quotes.", file=sys.stderr)
        return 1
    try:
        check_cli_token(args.token)
    except ValueError as exc:
        print(f"Authentication error: {exc}", file=sys.stderr)
        return 2
    try:
        business = resolve_business_profile(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2
    try:
        result = handle_call(args.caller, business=business)
    except ValueError as exc:
        print(f"Call error: {exc}", file=sys.stderr)
        return 2
    if not args.quiet:
        for line in result["transcript"]:
            print(f"{line['role'].title()}: {line['text']}")
    print(f"\nIntent: {result['intent']} | Route: {route_summary(result['route'])}")
    voice_ref = args.voice_ref or os.environ.get("VRA_VOICE_REF")
    synth_script = args.synth_script or os.environ.get("VRA_SYNTH_SCRIPT")
    if args.speak:
        if not voice_ref or not synth_script:
            print(
                "Voice error: --speak needs a voice reference audio and a "
                "synthesize script. Pass --voice-ref and --synth-script, or "
                "set VRA_VOICE_REF and VRA_SYNTH_SCRIPT.",
                file=sys.stderr,
            )
            return 2
    try:
        saved = speak(
            result["reply"],
            args.out,
            voice_ref=voice_ref if args.speak else None,
            synthesize_script=synth_script if args.speak else None,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Voice error: {exc}", file=sys.stderr)
        return 2
    print(f"Reply saved to {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
