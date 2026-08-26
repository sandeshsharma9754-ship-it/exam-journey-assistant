from typing import Any

from .input_handler import merge_input_sources
from .journey_planner import create_journey_plan
from .route_service import get_route, RouteServiceError
from .models import JourneyInput, JourneyPlan


class JourneyServiceError(Exception):
    """Raised when the complete journey planning process fails."""


def create_complete_journey_plan(
    form_data: dict[str, Any],
    admit_card_data: dict[str, Any] | None = None
) -> JourneyPlan:
    """
    Create a complete exam journey plan.

    Admit card is optional.

    Process:
        1. Merge form and optional admit-card data.
        2. Validate the student input.
        3. Calculate actual route distance and duration.
        4. Update journey travel duration.
        5. Run journey planner and risk engine.
        6. Return the final journey plan.
    """

    # --------------------------------------------------
    # STEP 1 — Validate and combine input sources
    # --------------------------------------------------

    try:
        journey = merge_input_sources(
            form_data=form_data,
            admit_card_data=admit_card_data
        )
    except Exception as exc:
        raise JourneyServiceError(
            f"Invalid journey input: {exc}"
        ) from exc

    # --------------------------------------------------
    # STEP 2 — Calculate route
    # --------------------------------------------------

    try:
        route = get_route(
            starting_location=journey.starting_location,
            destination=journey.exam_centre
        )
    except RouteServiceError as exc:
        raise JourneyServiceError(
            f"Unable to calculate travel route: {exc}"
        ) from exc

    # --------------------------------------------------
    # STEP 3 — Update journey with route duration
    # --------------------------------------------------

    journey_data = dict(journey.__dict__)

    journey_data["estimated_travel_minutes"] = (
        route.duration_minutes
    )

    updated_journey = JourneyInput(
        **journey_data
    )

    # --------------------------------------------------
    # STEP 4 — Generate final journey plan
    # --------------------------------------------------

    try:
        plan = create_journey_plan(
            updated_journey
        )
    except Exception as exc:
        raise JourneyServiceError(
            f"Unable to generate journey plan: {exc}"
        ) from exc

    return plan


def get_journey_summary(
    plan: JourneyPlan
) -> dict[str, Any]:
    """
    Convert the final journey plan into a frontend/API-friendly
    dictionary.
    """

    return {
        "departure_time": plan.departure_time.isoformat(),
        "expected_arrival": plan.expected_arrival.isoformat(),
        "total_travel_minutes": plan.total_travel_minutes,
        "buffer_minutes": plan.buffer_minutes,
        "risk_level": plan.risk_level,
        "same_day_travel": plan.same_day_travel,
        "previous_day_recommended": (
            plan.previous_day_recommended
        ),
        "recommendation": plan.recommendation,
    }


if __name__ == "__main__":

    # --------------------------------------------------
    # Integration test
    # --------------------------------------------------

    form_data = {
        "starting_location": "Bhopal, Madhya Pradesh",
        "exam_centre": "Indore, Madhya Pradesh",
        "exam_date": "2026-08-30",
        "reporting_time": "07:30",
        "gate_closing_time": "08:30",
        "estimated_travel_minutes": 0,
        "local_travel_minutes": 40,
        "transport_delay_minutes": 30,
        "departure_time": "2026-08-29 18:00",
    }

    try:
        plan = create_complete_journey_plan(
            form_data=form_data
        )

        print("\n" + "=" * 50)
        print("COMPLETE JOURNEY SERVICE TEST")
        print("=" * 50)

        print(
            f"Departure        : "
            f"{plan.departure_time}"
        )

        print(
            f"Expected Arrival : "
            f"{plan.expected_arrival}"
        )

        print(
            f"Travel Time      : "
            f"{plan.total_travel_minutes} minutes"
        )

        print(
            f"Buffer           : "
            f"{plan.buffer_minutes} minutes"
        )

        print(
            f"Risk Level       : "
            f"{plan.risk_level}"
        )

        print(
            f"Previous Day     : "
            f"{plan.previous_day_recommended}"
        )

        print(
            f"Recommendation   : "
            f"{plan.recommendation}"
        )

        print("=" * 50)

    except JourneyServiceError as exc:
        print(f"\nJourney Service Error: {exc}")