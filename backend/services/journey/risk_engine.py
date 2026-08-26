from datetime import datetime

from .models import JourneyInput, RiskResult
from .time_utils import parse_datetime, add_minutes, calculate_buffer


LOW_RISK_BUFFER = 120
MEDIUM_RISK_BUFFER = 60
HIGH_RISK_BUFFER = 30


def calculate_risk(
    journey: JourneyInput,
    departure_time: datetime
) -> RiskResult:

    reporting_datetime = parse_datetime(
        journey.exam_date,
        journey.reporting_time
    )

    gate_closing_datetime = parse_datetime(
        journey.exam_date,
        journey.gate_closing_time
    )

    total_travel_minutes = (
        journey.estimated_travel_minutes
        + journey.local_travel_minutes
        + journey.transport_delay_minutes
    )

    expected_arrival = add_minutes(
        departure_time,
        total_travel_minutes
    )

    reporting_buffer = calculate_buffer(
        expected_arrival,
        reporting_datetime
    )

    gate_buffer = calculate_buffer(
        expected_arrival,
        gate_closing_datetime
    )

    risk_level, recommendation = determine_risk(
        reporting_buffer,
        gate_buffer
    )

    previous_day_recommended = (
        risk_level in {"HIGH", "CRITICAL"}
    )

    same_day_travel = (
        departure_time.date() == expected_arrival.date()
    )

    return RiskResult(
        expected_arrival=expected_arrival,
        reporting_time=reporting_datetime,
        gate_closing_time=gate_closing_datetime,
        buffer_minutes=reporting_buffer,
        risk_level=risk_level,
        same_day_travel=same_day_travel,
        previous_day_recommended=previous_day_recommended,
        recommendation=recommendation
    )


def determine_risk(
    reporting_buffer: int,
    gate_buffer: int
) -> tuple[str, str]:

    if gate_buffer < 0:
        return (
            "CRITICAL",
            "Expected arrival is after gate closing time. "
            "The current journey is not safe."
        )

    if reporting_buffer < 0:
        return (
            "HIGH",
            "Expected arrival is after the reporting time. "
            "The student may miss important examination procedures."
        )

    if reporting_buffer < HIGH_RISK_BUFFER:
        return (
            "HIGH",
            "Very little buffer remains before reporting time. "
            "A safer journey is recommended."
        )

    if reporting_buffer < MEDIUM_RISK_BUFFER:
        return (
            "MEDIUM",
            "The journey is possible but the available buffer is limited."
        )

    if reporting_buffer < LOW_RISK_BUFFER:
        return (
            "MEDIUM",
            "The journey has a reasonable buffer, "
            "but additional travel margin is recommended."
        )

    return (
        "LOW",
        "The journey has sufficient buffer before reporting time."
    )