---
name: Bug report
about: Something in the agent does not work as described
title: "[Bug] "
labels: bug
---

## What happened

A clear description of what went wrong.

## How to reproduce

The exact command you ran, and the caller lines you used:

```bash
PYTHONPATH=src .venv/bin/python -m voice_receptionist_agent "your caller line here"
```

## What you expected

What the agent should have said or done.

## Business config

Did you use a custom `business.json`? If yes, paste the config with any real phone numbers removed.

## Environment

- Python version:
- Installed with: pip install -e . / requirements.txt
