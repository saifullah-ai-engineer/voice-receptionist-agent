"""Voice output interface.

This project is a text demo. Speech output is a pluggable integration
point, not included here. The stub below writes the reply text to a file
so any voice service can pick it up.

To speak replies in the business's own cloned voice, connect this module
to Saif's voice-clone-pipeline:

    https://github.com/saifullah-ai-engineer/voice-clone-pipeline

That project clones a voice with Sopro TTS v2-turbo and can lip-sync it
with MuseTalk. The wiring is: write the reply text with
write_reply_to_file, then run the pipeline's synthesize script on that
file with the business voice reference, then play the resulting audio on
the call. No voice audio is bundled in this repo, and no voice service
is called by default.
"""

from pathlib import Path


def write_reply_to_file(reply: str, path: str | Path) -> Path:
    """Write the reply text to a file for a voice service to speak."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(reply, encoding="utf-8")
    return target


def speak(reply: str, output_path: str | Path = "reply.txt") -> Path:
    """Default voice behaviour: save the reply text, do not call any service."""
    return write_reply_to_file(reply, output_path)
