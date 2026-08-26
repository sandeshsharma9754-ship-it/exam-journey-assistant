from datetime import datetime, timedelta

from .centre_models import (
    CentreInput,
    CentreResult,
    CentreSupportInfo,
)

from .centre_data import (
    DEFAULT_CHECKLIST,
    DEFAULT_WARNINGS,
    TRANSPORT_GUIDANCE,
)


class CentreServiceError(ValueError):
    """Raised when centre information is invalid."""


def create_centre_result(
    centre: CentreInput,
) -> CentreResult:
    """
    Generate practical examination-centre information
    from student-provided centre details.

    Admit-card upload is NOT required.
    """

    _validate_centre_input(centre)

    recommended_arrival_time = calculate_recommended_arrival(
        centre.reporting_time
    )

    support = CentreSupportInfo(
        recommended_arrival_time=recommended_arrival_time,
        transport_guidance=TRANSPORT_GUIDANCE,
        checklist=list(DEFAULT_CHECKLIST),
        warnings=list(DEFAULT_WARNINGS),
    )

    return CentreResult(
        centre_name=centre.centre_name,
        address=centre.address,
        city=centre.city,
        exam_date=centre.exam_date,
        reporting_time=centre.reporting_time,
        gate_closing_time=centre.gate_closing_time,
        support=support,
    )


def calculate_recommended_arrival(
    reporting_time: str,
) -> str:
    """
    Recommend reaching the centre 60 minutes before
    the official reporting time.
    """

    try:
        reporting = datetime.strptime(
            reporting_time,
            "%H:%M",
        )

    except ValueError as exc:
        raise CentreServiceError(
            "Reporting time must use HH:MM format."
        ) from exc

    recommended = reporting - timedelta(minutes=60)

    return recommended.strftime("%H:%M")


def _validate_centre_input(
    centre: CentreInput,
) -> None:

    required_fields = {
        "centre_name": centre.centre_name,
        "address": centre.address,
        "city": centre.city,
        "exam_date": centre.exam_date,
        "reporting_time": centre.reporting_time,
        "gate_closing_time": centre.gate_closing_time,
    }

    missing = [
        field
        for field, value in required_fields.items()
        if not value or not str(value).strip()
    ]

    if missing:
        raise CentreServiceError(
            "Missing required centre fields: "
            + ", ".join(missing)
        )

    try:
        datetime.strptime(
            centre.exam_date,
            "%Y-%m-%d",
        )
    except ValueError as exc:
        raise CentreServiceError(
            "Exam date must use YYYY-MM-DD format."
        ) from exc

    try:
        reporting = datetime.strptime(
            centre.reporting_time,
            "%H:%M",
        )

        gate_closing = datetime.strptime(
            centre.gate_closing_time,
            "%H:%M",
        )

    except ValueError as exc:
        raise CentreServiceError(
            "Reporting and gate closing times must use HH:MM format."
        ) from exc

    if gate_closing <= reporting:
        raise CentreServiceError(
            "Gate closing time must be later than reporting time."
        )