from datetime import datetime, timedelta

from .support_models import (
    SupportInput,
    SupportResult,
)

from .support_rules import (
    BASE_CHECKLIST,
    LOW_RISK_WARNING,
    MEDIUM_RISK_WARNING,
    HIGH_RISK_WARNING,
    CRITICAL_RISK_WARNING,
    LOW_DELAY_ACTION,
    MEDIUM_DELAY_ACTION,
    HIGH_DELAY_ACTION,
    CRITICAL_DELAY_ACTION,
    BACKUP_GUIDANCE,
)


class StudentSupportError(ValueError):
    """Raised when student-support input is invalid."""


def create_support_plan(
    support_input: SupportInput,
) -> SupportResult:
    """
    Generate a personalized exam-day support plan.

    Admit-card upload is not required.
    The plan works using examination and journey details.
    """

    _validate_input(support_input)

    departure = _parse_datetime(
        support_input.departure_time
    )

    expected_arrival = _parse_datetime(
        support_input.expected_arrival
    )

    exam_date = datetime.strptime(
        support_input.exam_date,
        "%Y-%m-%d",
    ).date()

    reporting_time = datetime.strptime(
        support_input.reporting_time,
        "%H:%M",
    ).time()

    gate_closing_time = datetime.strptime(
        support_input.gate_closing_time,
        "%H:%M",
    ).time()

    # --------------------------------------------------------
    # EXAM-DAY DATETIMES
    # --------------------------------------------------------

    reporting_datetime = datetime.combine(
        exam_date,
        reporting_time,
    )

    gate_datetime = datetime.combine(
        exam_date,
        gate_closing_time,
    )

    # Student should ideally reach the examination area
    # 60 minutes before official reporting.
    recommended_arrival = (
        reporting_datetime - timedelta(minutes=60)
    )

    # --------------------------------------------------------
    # DETERMINE WHETHER STUDENT ALREADY ARRIVES EARLY
    # --------------------------------------------------------

    # If expected arrival is already before the recommended
    # exam-day arrival time, the student does NOT need another
    # departure recommendation.
    already_arrived_early = (
        expected_arrival <= recommended_arrival
    )

    if already_arrived_early:

        leave_time = departure

        departure_label = (
            f"{leave_time.strftime('%Y-%m-%d %H:%M')} "
            "- Planned departure"
        )

        arrival_label = (
            f"{expected_arrival.strftime('%Y-%m-%d %H:%M')} "
            "- Expected arrival"
        )

    else:

        # Calculate actual journey duration.
        journey_duration = (
            expected_arrival - departure
        )

        # Calculate when the student should leave to reach
        # the examination area 60 minutes before reporting.
        calculated_leave_time = (
            recommended_arrival - journey_duration
        )

        # Never recommend leaving later than the student's
        # already supplied departure time.
        leave_time = min(
            calculated_leave_time,
            departure,
        )

        departure_label = (
            f"{leave_time.strftime('%Y-%m-%d %H:%M')} "
            "- Recommended departure"
        )

        arrival_label = (
            f"{recommended_arrival.strftime('%Y-%m-%d %H:%M')} "
            "- Recommended arrival at examination area"
        )

    # --------------------------------------------------------
    # WARNINGS
    # --------------------------------------------------------

    warnings = [
        _get_risk_warning(
            support_input.risk_level
        )
    ]

    if support_input.previous_day_recommended:
        warnings.append(
            "Previous-day arrival is recommended because "
            "the current journey carries significant risk."
        )

    if already_arrived_early:
        warnings.append(
            "The planned journey reaches the examination area "
            "before the recommended arrival time."
        )

    # --------------------------------------------------------
    # DELAY ACTION
    # --------------------------------------------------------

    delay_action = _get_delay_action(
        support_input.risk_level
    )

    # --------------------------------------------------------
    # TIMELINE
    # --------------------------------------------------------

    timeline = _build_timeline(
        departure_label=departure_label,
        arrival_label=arrival_label,
        reporting_datetime=reporting_datetime,
        gate_datetime=gate_datetime,
    )

    # --------------------------------------------------------
    # FINAL MESSAGE
    # --------------------------------------------------------

    final_message = _build_final_message(
        risk_level=support_input.risk_level,
        previous_day_recommended=(
            support_input.previous_day_recommended
        ),
        already_arrived_early=already_arrived_early,
    )

    return SupportResult(
        exam_date=support_input.exam_date,
        leave_time=leave_time.strftime(
            "%Y-%m-%d %H:%M"
        ),
        recommended_arrival_time=(
            recommended_arrival.strftime("%H:%M")
        ),
        preparation_checklist=list(
            BASE_CHECKLIST
        ),
        exam_day_timeline=timeline,
        warnings=warnings,
        delay_action=delay_action,
        backup_guidance=BACKUP_GUIDANCE,
        final_message=final_message,
    )


def _get_risk_warning(
    risk_level: str,
) -> str:

    risk = risk_level.upper()

    if risk == "LOW":
        return LOW_RISK_WARNING

    if risk == "MEDIUM":
        return MEDIUM_RISK_WARNING

    if risk == "HIGH":
        return HIGH_RISK_WARNING

    if risk == "CRITICAL":
        return CRITICAL_RISK_WARNING

    raise StudentSupportError(
        f"Unknown risk level: {risk_level}"
    )


def _get_delay_action(
    risk_level: str,
) -> str:

    risk = risk_level.upper()

    if risk == "LOW":
        return LOW_DELAY_ACTION

    if risk == "MEDIUM":
        return MEDIUM_DELAY_ACTION

    if risk == "HIGH":
        return HIGH_DELAY_ACTION

    if risk == "CRITICAL":
        return CRITICAL_DELAY_ACTION

    raise StudentSupportError(
        f"Unknown risk level: {risk_level}"
    )


def _build_timeline(
    departure_label: str,
    arrival_label: str,
    reporting_datetime: datetime,
    gate_datetime: datetime,
) -> list[str]:

    return [
        departure_label,
        arrival_label,
        (
            f"{reporting_datetime.strftime('%Y-%m-%d %H:%M')} "
            "- Official reporting time"
        ),
        (
            f"{gate_datetime.strftime('%Y-%m-%d %H:%M')} "
            "- Gate closing time"
        ),
    ]


def _build_final_message(
    risk_level: str,
    previous_day_recommended: bool,
    already_arrived_early: bool,
) -> str:

    risk = risk_level.upper()

    if risk == "CRITICAL":
        return (
            "Your current journey requires immediate attention. "
            "Consider a safer alternative or earlier arrival."
        )

    if risk == "HIGH":
        return (
            "Your journey has significant delay risk. "
            "Plan additional travel margin or consider arriving "
            "in the examination city earlier."
        )

    if risk == "MEDIUM":
        return (
            "Your journey is possible, but the available buffer "
            "is limited. Keep a backup transportation option ready."
        )

    if already_arrived_early:
        return (
            "Your planned journey reaches the examination area "
            "before the recommended arrival time. "
            "You have a comfortable preparation window."
        )

    if previous_day_recommended:
        return (
            "Consider reaching the examination city beforehand "
            "for a more reliable examination-day plan."
        )

    return (
        "Your examination-day plan has a comfortable travel buffer. "
        "Follow the preparation checklist and avoid unnecessary delays."
    )


def _parse_datetime(
    value: str,
) -> datetime:

    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                value,
                fmt,
            )
        except ValueError:
            continue

    raise StudentSupportError(
        "Datetime must use YYYY-MM-DD HH:MM format."
    )


def _validate_input(
    support_input: SupportInput,
) -> None:

    required = {
        "exam_date": support_input.exam_date,
        "reporting_time": support_input.reporting_time,
        "gate_closing_time": support_input.gate_closing_time,
        "risk_level": support_input.risk_level,
        "expected_arrival": support_input.expected_arrival,
        "departure_time": support_input.departure_time,
    }

    missing = [
        name
        for name, value in required.items()
        if value is None or not str(value).strip()
    ]

    if missing:
        raise StudentSupportError(
            "Missing required support fields: "
            + ", ".join(missing)
        )

    try:
        datetime.strptime(
            support_input.exam_date,
            "%Y-%m-%d",
        )

        datetime.strptime(
            support_input.reporting_time,
            "%H:%M",
        )

        datetime.strptime(
            support_input.gate_closing_time,
            "%H:%M",
        )

    except ValueError as exc:
        raise StudentSupportError(
            "Invalid exam date or examination time format."
        ) from exc

    if support_input.buffer_minutes is None:
        raise StudentSupportError(
            "Buffer minutes are required."
        )

    if support_input.risk_level.upper() not in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }:
        raise StudentSupportError(
            "Risk level must be LOW, MEDIUM, HIGH, or CRITICAL."
        )