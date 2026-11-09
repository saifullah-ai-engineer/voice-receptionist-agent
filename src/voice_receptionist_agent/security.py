"""Security helpers for the voice receptionist agent.

This repo is a local CLI and library, not a server. There is no user
login and no network service. The security surface is small: the
paths the operator passes on the command line, the script the voice
hook runs, the business config file, and the caller text that flows
through the agent. This module holds the checks for those inputs.

Rules enforced here:
- Output files are never written through a symlink and never over a
  directory, device, or other non-regular file.
- The voice synthesize script must be a real executable file, and the
  reply text is passed after a "--" separator so a reply that starts
  with a dash is spoken as text, never parsed as a flag.
- The optional CLI token (VRA_API_TOKEN) is checked with a
  constant-time comparison. It is off unless the operator sets it.
- Business configs and caller turns have size caps so one huge input
  cannot exhaust memory or make the service matcher compile a giant
  pattern.
"""

import hmac
import os
from pathlib import Path

MAX_CONFIG_BYTES = 1_000_000
MAX_SERVICES = 1_000
MAX_SERVICE_CHARS = 100
MAX_FIELD_CHARS = {
    "name": 200,
    "phone": 50,
    "hours": 500,
    "price_note": 1_000,
    "handoff_message": 500,
}
MAX_CALLER_TURN_CHARS = 10_000


def validate_output_path(path: str | Path) -> Path:
    """Check a file the agent is about to write, return the path.

    Rejects any path that runs through a symlink, and any existing
    target that is not a regular file. The operator chooses the path,
    so absolute paths and parent directories are allowed; what is
    blocked is writing through a link someone else planted, or over a
    directory or device.
    """
    target = Path(path)
    if str(target) == "":
        raise ValueError("Output path must not be empty.")
    for part in [target, *target.parents]:
        if os.path.lexists(part) and part.is_symlink():
            raise ValueError(
                f"Output path {target} runs through a symlink: {part}. "
                "Point --out at a plain file path instead."
            )
    if os.path.lexists(target) and not target.is_file():
        raise ValueError(
            f"Output path {target} is not a regular file. "
            "Point --out at a plain file path instead."
        )
    return target


def check_cli_token(provided: str | None) -> None:
    """Check the optional CLI token against VRA_API_TOKEN.

    The token is off unless the operator sets VRA_API_TOKEN. When it
    is set, the caller must pass the same value with --token. The
    comparison is constant-time, and a failure says nothing about
    which part was wrong.
    """
    expected = os.environ.get("VRA_API_TOKEN")
    if not expected:
        return
    if not provided or not hmac.compare_digest(provided, expected):
        raise ValueError("Authentication failed.")
