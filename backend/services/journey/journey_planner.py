from datetime import datetime, timedelta

from .models import JourneyInput, JourneyPlan
from .risk_engine import calculate_risk
from .time_utils import parse_datetime


def create_journey_plan(journey: JourneyInput) -> JourneyPlan:

    total_travel_minutes = (
        journey.estimated_travel_minutes
        + journey.local_travel_minutes
        + journey.transport_delay_minutes
    )

    if journey.departure_time:

        departure_time = datetime.strptime(
            journey.departure_time,
            "%Y-%m-%d %H:%M"
        )

    else:

        reporting_time = parse_datetime(
            journey.exam_date,
            journey.reporting_time
        )

        required_buffer = 120

        departure_time = (
            reporting_time
            - timedelta(minutes=required_buffer)
            - timedelta(minutes=total_travel_minutes)
        )

    risk_result = calculate_risk(
        journey,
        departure_time
    )

    return JourneyPlan(
        departure_time=departure_time,
        expected_arrival=risk_result.expected_arrival,
        total_travel_minutes=total_travel_minutes,
        buffer_minutes=risk_result.buffer_minutes,
        risk_level=risk_result.risk_level,
        same_day_travel=risk_result.same_day_travel,
        previous_day_recommended=risk_result.previous_day_recommended,
        recommendation=risk_result.recommendation
    )


def format_journey_plan(plan: JourneyPlan) -> str:

    return f"""
========================================
       EXAM JOURNEY PLAN
========================================

Departure Time       : {plan.departure_time.strftime("%d %b %Y, %I:%M %p")}
Expected Arrival     : {plan.expected_arrival.strftime("%d %b %Y, %I:%M %p")}

Total Travel Time    : {plan.total_travel_minutes} minutes
Available Buffer     : {plan.buffer_minutes} minutes

Risk Level           : {plan.risk_level}

Same-Day Travel      : {"Yes" if plan.same_day_travel else "No"}
Previous-Day Arrival : {"Recommended" if plan.previous_day_recommended else "Not Required"}

Recommendation:
{plan.recommendation}

========================================
"""


if __name__ == "__main__":

    test_journey = JourneyInput(
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

    plan = create_journey_plan(test_journey)

    print(format_journey_plan(plan))