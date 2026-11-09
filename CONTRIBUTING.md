# Contributing

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python examples/demo.py
```

## Tests

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/ -q
```

Every change needs a test that fails without it. Add tests for new
config behaviour, new intents, and new voice wiring.

## How the code is organised

- `src/voice_receptionist_agent/config.py`: business config loading and validation.
- `src/voice_receptionist_agent/graph.py`: the LangGraph call flow, greet to draft.
- `src/voice_receptionist_agent/intents.py`: rule-based intent classification and detail extraction.
- `src/voice_receptionist_agent/replies.py`: reply drafting from business facts only.
- `src/voice_receptionist_agent/router.py`: routing by intent and missing details.
- `src/voice_receptionist_agent/voice.py`: reply text output and optional Sopro TTS rendering.
- `src/voice_receptionist_agent/models.py`: shared types and the business profile.

## Rules for this repo

- The classifier stays deterministic and explainable. No paid model, no opaque API call in the default path.
- The agent only states facts from the business config. It never invents prices, hours, or availability.
- No em dash anywhere, in code, docs, or comments.
- No secret, .env file, voice audio, or personal data committed. Your own `business.json` is gitignored; only `business.example.json` is committed.
- Keep the demo working with no config, no key, and no phone line.
