# Security policy

## Reporting a vulnerability

Do not open a public issue for a security problem. Email the
maintainer at saifullahrao089@gmail.com with a description of the
problem and how to reproduce it. You will get a reply within a few
days, and the fix will be published as a new release.

## What this repo is

A local CLI and library, not a server. There is no user login, no
database, and no network service. The demo runs locally and calls no
external service unless you ask for voice rendering, which runs a
local script you choose. Keep that shape in mind: the protections
below cover the local inputs, not a hosted service.

## What is protected

- **Voice hook.** The synthesize script is run with a list of
  arguments and no shell, so caller words can never become a shell
  command. The script must be a real executable file, and the reply
  text is passed after a `--` separator so a reply starting with a
  dash is spoken as text, never parsed as a flag. Only point
  `--synth-script` at a script you trust: it runs with your user
  privileges and receives your voice reference audio.
- **Output files.** The reply is written only to the `--out` path
  you choose. A path that runs through a symlink is rejected, and an
  existing target that is not a regular file (a directory, a device)
  is rejected, so a planted link cannot redirect the write onto
  another file.
- **Business config.** Config files are capped at 1 MB, at most
  1,000 services, service names at most 100 characters, and the other
  text fields have length caps. A missing file, bad JSON, a missing or
  unknown field, a wrong type, or a value over a cap fails with a
  clear error and the agent does not run.
- **Caller text.** Each caller turn is capped at 10,000 characters.
  The raw caller message and the handoff reason are held in memory
  only for the call. They are never written to a file: the only file
  the agent writes is the reply text, which may address the caller by
  the name they gave. The CLI prints the caller transcript to the
  console by default; use `--quiet` when the console output is
  logged, so caller words do not end up in a log file.
- **Optional CLI token.** When `VRA_API_TOKEN` is set, the CLI needs
  `--token` with the same value, checked with a constant-time
  comparison. A wrong or missing token exits before any work is done.
  The token is off unless you set it, and it is a shared secret for
  one operator, not a user system: do not put it in a file that gets
  committed, and rotate it if it leaks.
- **Optional LLM hook.** The hook receives the raw caller text, so
  only use a hook you trust. It must not log, store, or send the
  caller text anywhere except to the model call it exists for. A hook
  that fails or answers with something unrecognised falls back to the
  rule-based classifier. No API key is handled by this repo; the hook
  owner holds their own key.
- **Dependencies.** Direct dependencies are pinned (`langgraph`).
  They were checked with `pip-audit` with no known vulnerabilities
  found at the time of the 0.2.2 release.

## What data the agent stores, and where

- `reply.txt` (or the `--out` path you choose): the reply text only.
  It may include the caller name from the reply. It is gitignored.
- `reply.wav` (only with `--speak`): the spoken reply audio. It is
  gitignored.
- `business.json`: your client business facts. It is gitignored. Do
  not commit it, and do not paste a real phone number or API key into
  an issue.
- Nothing else is written to disk. No call log, no database, no
  caller history is kept after the process ends.

## What is not protected

- This is a local tool. If you wrap it in a web service or a phone
  system, that wrapper owns authentication, rate limiting, TLS, and
  storage of call recordings. The optional `--token` only gates the
  local CLI; it does not protect a service you build around it.
- The phone line is not part of this repo. A telephony provider
  account and number are needed, and the provider's own security
  applies to the audio and the caller number.
- The voice reference audio is your business voice. Keep the file
  private; anyone with it and the synthesize script can render speech
  in that voice.
- The business config is trusted input. Anyone who can edit
  `business.json` can change what the agent says, including the phone
  number it gives out. Only the agency operator should be able to
  write that file.

## Supported versions

Only the latest release is supported with security fixes. Older
versions are not patched.
