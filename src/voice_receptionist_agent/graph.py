"""The call flow as a real LangGraph StateGraph.

Flow: greet -> classify -> collect -> route -> draft.
Each node reads and writes the shared call state.

The compiled graph is built once per process and reused for every
call. Rebuilding it on every call wasted about half the per-call time
and bought nothing, since the graph has no per-call state.
"""

from .intents import classify_intent, extract_details, extract_name, missing_details
from .models import BusinessProfile, CallState
from .replies import draft_reply, greeting
from .router import route_for

_COMPILED_APP = None


def _greet(state: CallState) -> CallState:
    business = state.get("business") or BusinessProfile()
    state["business"] = business
    state["transcript"] = [{"role": "receptionist", "text": greeting(business)}]
    return state


def _classify(state: CallState) -> CallState:
    text = " ".join(state.get("caller_turns", []))
    state["intent"] = classify_intent(text, state.get("llm_hook"))
    return state


def _collect(state: CallState) -> CallState:
    text = " ".join(state.get("caller_turns", []))
    state["caller_name"] = extract_name(text)
    state["details"] = extract_details(
        text, state["intent"], state.get("business")
    )
    state["missing"] = missing_details(state["intent"], state["details"])
    return state


def _route(state: CallState) -> CallState:
    state["route"] = route_for(state["intent"], state.get("missing", []))
    return state


def _draft(state: CallState) -> CallState:
    business = state.get("business") or BusinessProfile()
    reply = draft_reply(
        state["intent"], state["route"], state.get("details", {}),
        state.get("missing", []), state.get("caller_name"), business,
    )
    state["reply"] = reply
    state["transcript"] = state.get("transcript", []) + [
        {"role": "caller", "text": " ".join(state.get("caller_turns", []))},
        {"role": "receptionist", "text": reply},
    ]
    return state


def build_graph():
    """Build the receptionist call flow graph, once, and reuse it.

    The langgraph import happens here, not at module import, so code
    that only needs the classifier, the config loader, or the replies
    does not pay the langgraph import cost.
    """
    global _COMPILED_APP
    if _COMPILED_APP is not None:
        return _COMPILED_APP
    from langgraph.graph import END, StateGraph

    graph = StateGraph(CallState)
    graph.add_node("greet", _greet)
    graph.add_node("classify", _classify)
    graph.add_node("collect", _collect)
    graph.add_node("route", _route)
    graph.add_node("draft", _draft)
    graph.set_entry_point("greet")
    graph.add_edge("greet", "classify")
    graph.add_edge("classify", "collect")
    graph.add_edge("collect", "route")
    graph.add_edge("route", "draft")
    graph.add_edge("draft", END)
    _COMPILED_APP = graph.compile()
    return _COMPILED_APP


def handle_call(caller_turns, business=None, llm_hook=None) -> CallState:
    """Run one simulated call through the graph and return the final state."""
    app = build_graph()
    result = app.invoke({
        "caller_turns": list(caller_turns),
        "business": business or BusinessProfile(),
        "llm_hook": llm_hook,
    })
    return result
