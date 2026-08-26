from typing import Any

from .models import JourneyInput


class InputValidationError(ValueError):
    """Raised when student journey input is invalid."""


# These are the fields that the student/system must provide
# before route calculation.
REQUIRED_FIELDS = {
    "starting_location",
    "exam_centre",
    "exam_date",
    "reporting_time",
    "gate_closing_time",
}


def build_journey_input(
    data: dict[str, Any]
) -> JourneyInput:
    """
    Convert raw student/admit-card data into a validated
    JourneyInput.

    estimated_travel_minutes is NOT a student-required field.
    It is calculated later by RouteService.
    """

    if not isinstance(data, dict):
        raise InputValidationError(
            "Journey input must be provided as an object."
        )

    cleaned_data = _clean_input(data)

    _validate_required_fields(cleaned_data)
    _validate_values(cleaned_data)

    # Route duration is calculated after input validation.
    # Until then, use zero as the placeholder value.
    if cleaned_data.get("estimated_travel_minutes") is None:
        cleaned_data["estimated_travel_minutes"] = 0

    # Optional travel values default to zero.
    if cleaned_data.get("local_travel_minutes") is None:
        cleaned_data["local_travel_minutes"] = 0

    if cleaned_data.get("transport_delay_minutes") is None:
        cleaned_data["transport_delay_minutes"] = 0

    try:
        return JourneyInput(**cleaned_data)

    except Exception as exc:
        raise InputValidationError(
            f"Invalid journey data: {exc}"
        ) from exc


def _clean_input(
    data: dict[str, Any]
) -> dict[str, Any]:
    """
    Remove unnecessary whitespace from string values.
    """

    cleaned = {}

    for key, value in data.items():

        if isinstance(value, str):
            value = value.strip()

            if value == "":
                value = None

        cleaned[key] = value

    return cleaned


def _validate_required_fields(
    data: dict[str, Any]
) -> None:
    """
    Validate fields required for journey planning.
    """

    missing_fields = [
        field
        for field in REQUIRED_FIELDS
        if data.get(field) is None
    ]

    if missing_fields:
        raise InputValidationError(
            "Missing required fields: "
            + ", ".join(sorted(missing_fields))
        )


def _validate_values(
    data: dict[str, Any]
) -> None:
    """
    Validate basic journey values.
    """

    if not isinstance(
        data["starting_location"],
        str
    ) or not data["starting_location"].strip():

        raise InputValidationError(
            "Starting location cannot be empty."
        )

    if not isinstance(
        data["exam_centre"],
        str
    ) or not data["exam_centre"].strip():

        raise InputValidationError(
            "Exam centre cannot be empty."
        )

    _validate_non_negative_number(
        data.get("estimated_travel_minutes", 0),
        "estimated_travel_minutes"
    )

    _validate_non_negative_number(
        data.get("local_travel_minutes", 0),
        "local_travel_minutes"
    )

    _validate_non_negative_number(
        data.get("transport_delay_minutes", 0),
        "transport_delay_minutes"
    )


def _validate_non_negative_number(
    value: Any,
    field_name: str
) -> None:

    if value is None:
        return

    try:
        numeric_value = float(value)

    except (TypeError, ValueError) as exc:

        raise InputValidationError(
            f"{field_name} must be a number."
        ) from exc

    if numeric_value < 0:

        raise InputValidationError(
            f"{field_name} cannot be negative."
        )


def merge_input_sources(
    form_data: dict[str, Any],
    admit_card_data: dict[str, Any] | None = None
) -> JourneyInput:
    """
    Merge student form data with optional admit-card data.

    Priority:
        1. Admit-card extracted data
        2. Explicit student form data

    Therefore, the student can use the system without
    uploading an admit card.
    """

    merged_data = {}

    if admit_card_data:
        merged_data.update(admit_card_data)

    merged_data.update(form_data)

    return build_journey_input(merged_data)