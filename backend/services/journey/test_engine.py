from datetime import datetime

from .models import JourneyInput
from .journey_planner import create_journey_plan


def run_test(test_name: str, journey: JourneyInput):
    """
    Run one journey test and display the result.
    """

    plan = create_journey_plan(journey)

    print("\n" + "=" * 50)
    print(f"TEST: {test_name}")
    print("=" * 50)

    print(f"Departure Time    : {plan.departure_time}")
    print(f"Expected Arrival  : {plan.expected_arrival}")
    print(f"Travel Time       : {plan.total_travel_minutes} minutes")
    print(f"Buffer            : {plan.buffer_minutes} minutes")
    print(f"Risk Level        : {plan.risk_level}")
    print(f"Previous Day      : {plan.previous_day_recommended}")
    print(f"Recommendation    : {plan.recommendation}")


# --------------------------------------------------
# TEST 1 — LOW RISK
# --------------------------------------------------

safe_journey = JourneyInput(
    starting_location="Bhopal",
    exam_centre="XYZ School, Indore",
    exam_date="2026-08-30",
    reporting_time="07:30",
    gate_closing_time="08:30",
    estimated_travel_minutes=240,
    local_travel_minutes=40,
    transport_delay_minutes=0,
    departure_time="2026-08-29 20:00"
)


# --------------------------------------------------
# TEST 2 — HIGH RISK
# --------------------------------------------------

high_risk_journey = JourneyInput(
    starting_location="Bhopal",
    exam_centre="XYZ School, Indore",
    exam_date="2026-08-30",
    reporting_time="07:30",
    gate_closing_time="08:30",
    estimated_travel_minutes=240,
    local_travel_minutes=40,
    transport_delay_minutes=0,
    departure_time="2026-08-30 05:30"
)


# --------------------------------------------------
# TEST 3 — CRITICAL RISK
# --------------------------------------------------

critical_journey = JourneyInput(
    starting_location="Bhopal",
    exam_centre="XYZ School, Indore",
    exam_date="2026-08-30",
    reporting_time="07:30",
    gate_closing_time="08:30",
    estimated_travel_minutes=240,
    local_travel_minutes=40,
    transport_delay_minutes=30,
    departure_time="2026-08-30 06:00"
)


if __name__ == "__main__":

    run_test(
        "LOW RISK — Safe Journey",
        safe_journey
    )

    run_test(
        "HIGH RISK — Limited Buffer",
        high_risk_journey
    )

    run_test(
        "CRITICAL — Gate Closing Risk",
        critical_journey
    )