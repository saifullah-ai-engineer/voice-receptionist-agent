"""Tests for the security checks: paths, voice hook, token, PII, caps."""

import json
import os
import stat

import pytest

from voice_receptionist_agent import __version__
from voice_receptionist_agent.__main__ import main
from voice_receptionist_agent.config import (
    business_profile_from_dict,
    load_business_profile,
)
from voice_receptionist_agent.graph import handle_call
from voice_receptionist_agent.security import (
    MAX_CALLER_TURN_CHARS,
    MAX_CONFIG_BYTES,
    check_cli_token,
    validate_output_path,
)
from voice_receptionist_agent.voice import speak, speak_audio
from tests.test_config import EXAMPLE


def _stub_script(tmp_path, record):
    """A fake synthesize script that records its argv and writes audio."""
    script = tmp_path / "synthesize.sh"
    script.write_text(
        "#!/bin/bash\n"
        f"printf '%s\\n' \"$@\" > \"{record}\"\n"
        "out=\"\"\n"
        "prev=\"\"\n"
        "for arg in \"$@\"; do\n"
        "  if [ \"$prev\" = \"--out\" ]; then out=\"$arg\"; fi\n"
        "  prev=\"$arg\"\n"
        "done\n"
        "printf 'FAKEAUDIO' > \"$out\"\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def _config_file(tmp_path, data=None):
    cfg = tmp_path / "business.json"
    cfg.write_text(json.dumps(data or EXAMPLE), encoding="utf-8")
    return cfg


# --- Output paths ---


def test_output_path_inside_tmpdir_is_accepted(tmp_path):
    assert validate_output_path(tmp_path / "reply.txt").name == "reply.txt"


def test_output_path_through_a_symlink_is_rejected(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        validate_output_path(link / "reply.txt")


def test_output_path_that_is_itself_a_symlink_is_rejected(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("innocent", encoding="utf-8")
    link = tmp_path / "reply.txt"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        validate_output_path(link)


def test_output_path_that_is_a_directory_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="not a regular file"):
        validate_output_path(tmp_path)


def test_write_reply_refuses_a_symlinked_target(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("innocent", encoding="utf-8")
    link = tmp_path / "reply.txt"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        speak("Hello", link)
    assert target.read_text() == "innocent"


# --- Voice hook ---


def test_voice_script_must_be_executable(tmp_path):
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"fake reference audio")
    script = tmp_path / "synthesize.sh"
    script.write_text("#!/bin/bash\necho hi\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not executable"):
        speak_audio("Hello", voice_ref=ref, synthesize_script=script,
                    output_path=tmp_path / "reply.wav")


def test_reply_is_passed_after_double_dash(tmp_path):
    record = tmp_path / "argv.txt"
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"fake reference audio")
    speak_audio(
        "--help",
        voice_ref=ref,
        synthesize_script=_stub_script(tmp_path, record),
        output_path=tmp_path / "reply.wav",
    )
    args = record.read_text().splitlines()
    assert args[-2] == "--"
    assert args[-1] == "--help"


# --- Caller PII ---


def test_saved_reply_never_contains_the_raw_caller_message(tmp_path):
    result = handle_call(
        ["Hi, my name is Ayesha, my card number is 4111 1111, "
         "I need a refund about my cleaning"],
    )
    saved = speak(result["reply"], tmp_path / "reply.txt")
    saved_text = saved.read_text()
    assert "4111" not in saved_text
    assert "my card number is" not in saved_text
    assert "refund about my cleaning" not in saved_text


def test_cli_quiet_hides_the_caller_transcript(tmp_path, capsys, monkeypatch):
    cfg = _config_file(tmp_path)
    out = tmp_path / "reply.txt"
    code = main([
        "--config", str(cfg), "--out", str(out), "--quiet",
        "Hi, my name is Ayesha, I want to book a cleaning",
    ])
    assert code == 0
    captured = capsys.readouterr()
    assert "Ayesha" not in captured.out
    assert "book a cleaning" not in captured.out
    assert "Intent:" in captured.out


def test_cli_without_quiet_shows_the_transcript(tmp_path, capsys):
    cfg = _config_file(tmp_path)
    out = tmp_path / "reply.txt"
    code = main([
        "--config", str(cfg), "--out", str(out),
        "Hi, my name is Ayesha, I want to book a cleaning",
    ])
    assert code == 0
    captured = capsys.readouterr()
    assert "Ayesha" in captured.out


# --- Optional CLI token ---


def test_token_check_passes_when_unset():
    check_cli_token(None)
    check_cli_token("anything")


def test_token_check_passes_with_the_right_token(monkeypatch):
    monkeypatch.setenv("VRA_API_TOKEN", "secret-token")
    check_cli_token("secret-token")


def test_token_check_fails_with_wrong_or_missing_token(monkeypatch):
    monkeypatch.setenv("VRA_API_TOKEN", "secret-token")
    with pytest.raises(ValueError, match="Authentication failed"):
        check_cli_token("wrong-token")
    with pytest.raises(ValueError, match="Authentication failed"):
        check_cli_token(None)


def test_cli_token_gates_the_run(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("VRA_API_TOKEN", "secret-token")
    cfg = _config_file(tmp_path)
    out = tmp_path / "reply.txt"
    assert main([
        "--config", str(cfg), "--out", str(out),
        "--token", "wrong-token", "Hello",
    ]) == 2
    assert main([
        "--config", str(cfg), "--out", str(out), "Hello",
    ]) == 2
    assert main([
        "--config", str(cfg), "--out", str(out),
        "--token", "secret-token", "Hello",
    ]) == 0


# --- Config and caller caps ---


def test_config_file_over_the_size_cap_is_rejected(tmp_path):
    big = tmp_path / "business.json"
    big.write_bytes(b"x" * (MAX_CONFIG_BYTES + 1))
    with pytest.raises(ValueError, match="larger than"):
        load_business_profile(big)


def test_more_than_1000_services_is_rejected():
    data = dict(EXAMPLE)
    data["services"] = [f"service {i}" for i in range(1001)]
    with pytest.raises(ValueError, match="more than"):
        business_profile_from_dict(data)


def test_service_name_over_the_length_cap_is_rejected():
    data = dict(EXAMPLE)
    data["services"] = ["x" * 101]
    with pytest.raises(ValueError, match="no longer than"):
        business_profile_from_dict(data)


def test_field_over_the_length_cap_is_rejected():
    data = dict(EXAMPLE)
    data["name"] = "x" * 201
    with pytest.raises(ValueError, match="longer than"):
        business_profile_from_dict(data)


def test_caller_turn_over_the_length_cap_is_rejected():
    with pytest.raises(ValueError, match="longer than"):
        handle_call(["x" * (MAX_CALLER_TURN_CHARS + 1)])


# --- Version ---


def test_version_is_current(capsys):
    assert __version__ == "0.2.2"
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == "0.2.2"
