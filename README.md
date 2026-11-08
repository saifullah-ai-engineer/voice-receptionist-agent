# voice-receptionist-agent

A voice receptionist agent for small businesses. It answers an inbound call, greets the caller, understands the intent, collects the details it needs, routes the call, and drafts a reply in the business's voice.

It is built on Saif's voice work: the reply text plugs into the [voice-clone-pipeline](https://github.com/saifullah-ai-engineer/voice-clone-pipeline) for speech output in the business's own cloned voice.

## What it does

- Greets the caller with the business name.
- Understands five intents: booking, price question, opening hours, human handoff, and other.
- Collects the caller's name, the service, and the day and time for bookings.
- Asks a clear follow-up question when a detail is missing, instead of guessing.
- Routes the call: confirm a booking, answer from business facts, or hand off to a human.
- Drafts a reply using only the business facts and the caller's own words.
- Saves the reply text to a file so a voice service can speak it.

## 30 second demo

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python examples/demo.py
```

You will see three simulated calls: a booking, a price question, and a human handoff, each with its transcript and outcome. No paid API, no phone line, no voice service. Text only.

Try a call of your own:

```bash
PYTHONPATH=src .venv/bin/python -m voice_receptionist_agent "Hi, my name is Ayesha, I want to book a cleaning on Saturday at 10am"
```

## Call flows

- Booking: greet, classify as booking, collect service and day, confirm the slot, note that the team will call back to confirm.
- Price question: greet, classify as pricing, answer from the business price note, offer to book.
- Opening hours: greet, classify as hours, answer with the business hours, offer to book.
- Human handoff: greet, classify as handoff, connect the caller to a team member and give the business phone number.
- Missing details: greet, classify, ask for the missing service or day, wait for the caller.

## How it works

A real LangGraph `StateGraph` in `src/voice_receptionist_agent/graph.py` runs five nodes: greet, classify, collect, route, draft. The intent classifier is rule-based by default and an optional LLM hook can be passed in; if the hook fails or returns something unknown, the rules take over. Routing lives in `router.py`, reply drafting in `replies.py`, and the voice output stub in `voice.py`.

## How to connect voice

The demo is text-based. The phone line and voice synthesis are integration points, not included.

1. Clone the caller's voice or use the business voice with the [voice-clone-pipeline](https://github.com/saifullah-ai-engineer/voice-clone-pipeline) (Sopro TTS v2-turbo, plus MuseTalk lip-sync if you want video).
2. Point `voice.speak` at the pipeline: it already writes the reply text to `reply.txt`, so run the pipeline's synthesize script on that file with the business voice reference.
3. Play the resulting audio on the call. For a real phone line, put a telephony provider (for example Twilio) in front of this agent: speech-to-text in, this graph, text-to-speech out.

## Configuration

Edit `BusinessProfile` in `src/voice_receptionist_agent/models.py`, or pass your own profile to `handle_call`: business name, services, hours, price note, handoff message, and phone number. The defaults describe a dental clinic and are only an example; change them before using this for a real business.

## Honest limits

- This is a text demo. It does not answer a real phone call and it does not speak.
- The intent classifier is keyword-based by default. It handles the common phrasings well and asks for clarification when it is unsure, but it is not a full speech understanding system.
- It only knows the facts in the business profile. It never invents prices, hours, or availability.
- It does not store call recordings or caller data. Add your own storage if you need call logs.

## Tests

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
```

20 tests cover each intent, the LLM hook and its fallback, name and detail extraction, missing details, routing, full end-to-end calls, a custom business profile, and the voice stub.

## License

MIT. See LICENSE.
