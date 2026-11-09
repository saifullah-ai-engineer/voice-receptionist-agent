"""Voice output interface.

This project is a text demo by default. Speech output is a pluggable
integration point, and the Sopro TTS wiring below is real: it runs the
voice-clone-pipeline synthesize script with the business voice
reference and produces spoken audio for the reply.

To speak replies in the business's own cloned voice, connect this
module to Saif's voice-clone-pipeline:

    https://github.com/saifullah-ai-engineer/voice-clone-pipeline

That project clones a voice with Sopro TTS v2-turbo and can lip-sync
it with MuseTalk. The wiring is: write the reply text with
write_reply_to_file, then run the pipeline's synthesize script on that
text with the business voice reference, then play the resulting audio
on the call. No voice audio is bundled in this repo, and no voice
service is called unless you ask for it with speak_audio or the
--speak flag.
"""

import subprocess
from pathlib import Path


def write_reply_to_file(reply: str, path: str | Path) -> Path:
    """Write the reply text to a file for a voice service to speak."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(reply, encoding="utf-8")
    return target


def speak_audio(
    reply: str,
    voice_ref: str | Path,
    synthesize_script: str | Path,
    output_path: str | Path = "reply.wav",
    timeout: int = 300,
) -> Path:
    """Render the reply as spoken audio with Sopro TTS and return the audio file.

    voice_ref is the business voice reference audio (5 to 20 seconds,
    wav). synthesize_script is the voice-clone-pipeline synthesize
    script, which runs soprotts with the right environment. Both must
    exist on disk. A failure raises a clear error and no audio file is
    returned.
    """
    script = Path(synthesize_script)
    if not script.is_file():
        raise FileNotFoundError(
            f"Voice synthesize script not found: {script}. "
            "Use the voice-clone-pipeline scripts/synthesize.sh, or leave "
            "voice off and the reply stays as text."
        )
    ref = Path(voice_ref)
    if not ref.is_file():
        raise FileNotFoundError(
            f"Voice reference audio not found: {ref}. "
            "Record 5 to 20 seconds of the business voice and pass its path."
        )
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            [str(script), "--ref", str(ref), "--out", str(out), reply],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Voice synthesis timed out after {timeout} seconds. "
            "Try a shorter reply or a faster machine."
        ) from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        detail = detail[-1] if detail else "no error output"
        raise RuntimeError(
            f"Voice synthesis failed (exit {result.returncode}): {detail}"
        )
    if not out.is_file() or out.stat().st_size == 0:
        raise RuntimeError(
            f"Voice synthesis finished but produced no audio at {out}."
        )
    return out


def speak(
    reply: str,
    output_path: str | Path = "reply.txt",
    voice_ref: str | Path | None = None,
    synthesize_script: str | Path | None = None,
    audio_path: str | Path | None = None,
) -> Path:
    """Default voice behaviour: save the reply text, do not call any service.

    Pass voice_ref and synthesize_script together to also render spoken
    audio. Then the audio path is returned instead of the text path.
    Passing only one of them is an error, so a half-configured voice
    setup fails loudly instead of silently staying text-only.
    """
    text_path = write_reply_to_file(reply, output_path)
    if voice_ref is None and synthesize_script is None:
        return text_path
    if voice_ref is None or synthesize_script is None:
        raise ValueError(
            "Voice needs both a voice reference audio (--voice-ref) and a "
            "synthesize script (--synth-script). Pass both, or neither for "
            "text only."
        )
    audio = Path(audio_path) if audio_path else text_path.with_suffix(".wav")
    return speak_audio(reply, voice_ref, synthesize_script, audio)
