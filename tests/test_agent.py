"""Tests for the voice receptionist agent."""

from voice_receptionist_agent.graph import handle_call
from voice_receptionist_agent.intents import classify_intent, extract_details, extract_name, missing_details
from voice_receptionist_agent.models import BusinessProfile, Intent, Route
from voice_receptionist_agent.replies import draft_reply, greeting
from voice_receptionist_agent.router import route_for, route_summary
from voice_receptionist_agent.voice import speak


def test_booking_intent():
    assert classify_intent("I want to book an appointment for Saturday") == Intent.BOOKING


def test_pricing_intent():
    assert classify_intent("How much does a cleaning cost?") == Intent.PRICING


def test_hours_intent():
    assert classify_intent("What are your opening hours?") == Intent.HOURS


def test_human_intent():
    assert classify_intent("Can I speak to a real person please?") == Intent.HUMAN


def test_other_intent_when_nothing_matches():
    assert classify_intent("The weather is nice today") == Intent.OTHER


def test_llm_hook_overrides_rules():
    assert classify_intent("anything at all", llm_hook=lambda text: "pricing") == Intent.PRICING


def test_broken_llm_hook_falls_back_to_rules():
    def broken(text):
        raise RuntimeError("model down")

    assert classify_intent("How much is a checkup?", llm_hook=broken) == Intent.PRICING


def test_name_extraction():
    assert extract_name("Hi, my name is Ayesha Khan") == "Ayesha Khan"
    assert extract_name("This is Bilal, I need a cleaning") == "Bilal"


def test_booking_collects_service_and_day():
    details = extract_details("I want to book a cleaning on Saturday at 10am", Intent.BOOKING)
    assert details["service"] == "cleaning"
    assert details["day"] == "Saturday"
    assert details["time"] == "10am"


def test_missing_details_for_booking():
    assert missing_details(Intent.BOOKING, {}) == ["service", "day"]
    assert missing_details(Intent.BOOKING, {"service": "cleaning"}) == ["day"]
    assert missing_details(Intent.BOOKING, {"service": "cleaning", "day": "Saturday"}) == []


def test_routing():
    assert route_for(Intent.HUMAN, []) == Route.HUMAN
    assert route_for(Intent.BOOKING, ["day"]) == Route.CLARIFY
    assert route_for(Intent.BOOKING, []) == Route.BOOK
    assert route_for(Intent.PRICING, []) == Route.ANSWER
    assert route_for(Intent.OTHER, []) == Route.HUMAN
    assert "Booking" in route_summary(Route.BOOK)


def test_full_booking_call():
    result = handle_call(["Hi, my name is Ayesha, I want to book a cleaning on Saturday at 10am"])
    assert result["intent"] == Intent.BOOKING
    assert result["route"] == Route.BOOK
    assert result["caller_name"] == "Ayesha"
    assert "cleaning" in result["reply"]
    assert "Saturday" in result["reply"]
    assert len(result["transcript"]) == 3


def test_full_price_call():
    result = handle_call(["How much does a checkup cost?"])
    assert result["intent"] == Intent.PRICING
    assert result["route"] == Route.ANSWER
    assert "2,000" in result["reply"]


def test_full_hours_call():
    result = handle_call(["What time do you close?"])
    assert result["intent"] == Intent.HOURS
    assert "9am to 6pm" in result["reply"]


def test_full_human_handoff_call():
    result = handle_call(["I want to speak to a real person about a refund"])
    assert result["intent"] == Intent.HUMAN
    assert result["route"] == Route.HUMAN
    assert "team" in result["reply"]


def test_missing_details_asks_a_question():
    result = handle_call(["I want to book an appointment"])
    assert result["route"] == Route.CLARIFY
    assert "Which service" in result["reply"] or "which day" in result["reply"].lower()


def test_greeting_uses_business_name():
    business = BusinessProfile(name="Sunrise Salon")
    assert "Sunrise Salon" in greeting(business)


def test_custom_business_profile():
    business = BusinessProfile(name="Sunrise Salon", hours="10am to 8pm")
    result = handle_call(["When do you open?"], business=business)
    assert "Sunrise Salon" in result["transcript"][0]["text"]
    assert "10am to 8pm" in result["reply"]


def test_voice_stub_writes_reply_to_file(tmp_path):
    path = speak("Hello, how can I help?", tmp_path / "reply.txt")
    assert path.read_text() == "Hello, how can I help?"


def test_draft_reply_never_invents_a_price():
    business = BusinessProfile()
    reply = draft_reply(Intent.OTHER, Route.HUMAN, {}, [], None, business)
    assert "2,000" not in reply and "3,500" not in reply


def test_graph_is_built_once_and_reused():
    from voice_receptionist_agent.graph import build_graph

    assert build_graph() is build_graph()


def test_repeated_calls_stay_fast_and_consistent():
    first = handle_call(["How much does a checkup cost?"])
    second = handle_call(["How much does a checkup cost?"])
    assert first["reply"] == second["reply"]
    assert first["intent"] == second["intent"]


def test_multi_word_service_from_profile():
    from voice_receptionist_agent.intents import extract_details

    business = BusinessProfile(
        name="Smile Clinic",
        services=["root canal", "cleaning"],
    )
    details = extract_details("I want to book a root canal on Monday", Intent.BOOKING, business)
    assert details["service"] == "root canal"


def test_extract_details_without_business_keeps_old_behaviour():
    details = extract_details("I want to book a cleaning on Saturday", Intent.BOOKING)
    assert details["service"] == "cleaning"


def test_clarify_reply_caps_a_long_service_list():
    business = BusinessProfile(
        name="Big Business",
        services=[f"service {i:04d}" for i in range(100)],
    )
    result = handle_call(["I want to book an appointment on Friday"], business=business)
    assert result["route"] == Route.CLARIFY
    assert "service 0000" in result["reply"]
    assert "service 0007" in result["reply"]
    assert "service 0008" not in result["reply"]
    assert "and 92 more" in result["reply"]
    assert len(result["reply"]) < 500


def test_clarify_reply_lists_every_service_for_a_small_business():
    business = BusinessProfile(
        name="Small Salon",
        services=["haircut", "colouring", "styling"],
    )
    result = handle_call(["I want to book an appointment on Friday"], business=business)
    assert result["route"] == Route.CLARIFY
    assert "haircut, colouring, styling" in result["reply"]
    assert "more" not in result["reply"]
