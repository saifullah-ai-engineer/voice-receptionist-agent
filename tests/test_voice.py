"""Tests for voice output, including the real Sopro TTS wiring."""

import stat

import pytest

from voice_receptionist_agent.voice import speak, speak_audio


def _stub_script(tmp_path):
    """A fake synthesize script that writes a marker audio file."""
    script = tmp_path / "synthesize.sh"
    script.write_text(
        "#!/bin/bash\n"
        "out=\"\"\n"
        "while [ $# -gt 0 ]; do\n"
        "  if [ \"$1\" = \"--out\" ]; then out=\"$2\"; shift 2; else shift; fi\n"
        "done\n"
        "printf 'FAKEAUDIO' > \"$out\"\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def test_speak_audio_runs_the_script(tmp_path):
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"fake reference audio")
    audio = speak_audio(
        "Hello, how can I help?",
        voice_ref=ref,
        synthesize_script=_stub_script(tmp_path),
        output_path=tmp_path / "reply.wav",
    )
    assert audio.read_bytes() == b"FAKEAUDIO"


def test_speak_audio_fails_clearly_when_script_is_missing(tmp_path):
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"fake reference audio")
    with pytest.raises(FileNotFoundError, match="synthesize script not found"):
        speak_audio(
            "Hello",
            voice_ref=ref,
            synthesize_script=tmp_path / "nope.sh",
            output_path=tmp_path / "reply.wav",
        )


def test_speak_audio_fails_clearly_when_voice_is_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="reference audio not found"):
        speak_audio(
            "Hello",
            voice_ref=tmp_path / "nope.wav",
            synthesize_script=_stub_script(tmp_path),
            output_path=tmp_path / "reply.wav",
        )


def test_speak_with_one_voice_arg_fails_loudly(tmp_path):
    with pytest.raises(ValueError, match="both"):
        speak("Hello", tmp_path / "reply.txt", voice_ref=tmp_path / "voice.wav")


def test_speak_with_voice_renders_audio_and_text(tmp_path):
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"fake reference audio")
    audio = speak(
        "Hello, how can I help?",
        tmp_path / "reply.txt",
        voice_ref=ref,
        synthesize_script=_stub_script(tmp_path),
    )
    assert audio.suffix == ".wav"
    assert audio.read_bytes() == b"FAKEAUDIO"
    assert (tmp_path / "reply.txt").read_text() == "Hello, how can I help?"


def test_speak_still_text_only_by_default(tmp_path):
    path = speak("Hello", tmp_path / "reply.txt")
    assert path.suffix == ".txt"
    assert path.read_text() == "Hello"
    assert not (tmp_path / "reply.wav").exists()
