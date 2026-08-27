from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.services.journey.journey_service import (
    create_complete_journey_plan,
    get_journey_summary,
    JourneyServiceError,
)

from backend.services.centre.centre_service import (
    create_centre_result,
    CentreServiceError,
)

from backend.services.centre.centre_models import CentreInput


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Exam Journey Assistant API",
    description=(
        "Exam Journey Assistant provides safe journey planning, "
        "exam-centre intelligence, and student support for "
        "competitive examination candidates."
    ),
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
  allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
],
    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# JOURNEY REQUEST
# ============================================================

class JourneyRequest(BaseModel):
    starting_location: str = Field(
        ...,
        min_length=2,
        description="Student's starting location",
    )

    exam_centre: str = Field(
        ...,
        min_length=2,
        description="Exam centre or examination location",
    )

    exam_date: str

    reporting_time: str

    gate_closing_time: str

    local_travel_minutes: int = Field(
        default=0,
        ge=0,
    )

    transport_delay_minutes: int = Field(
        default=0,
        ge=0,
    )

    departure_time: str | None = None

    admit_card_data: dict[str, Any] | None = None


# ============================================================
# CENTRE REQUEST
# ============================================================

class CentreRequest(BaseModel):
    centre_name: str = Field(
        ...,
        min_length=2,
    )

    address: str = Field(
        ...,
        min_length=2,
    )

    city: str = Field(
        ...,
        min_length=2,
    )

    exam_date: str

    reporting_time: str

    gate_closing_time: str

    latitude: float | None = None

    longitude: float | None = None


# ============================================================
# COMPLETE EXAM PLAN REQUEST
# ============================================================

class CompleteExamPlanRequest(BaseModel):
    starting_location: str = Field(
        ...,
        min_length=2,
    )

    exam_centre: str = Field(
        ...,
        min_length=2,
    )

    exam_date: str

    reporting_time: str

    gate_closing_time: str

    local_travel_minutes: int = Field(
        default=0,
        ge=0,
    )

    transport_delay_minutes: int = Field(
        default=0,
        ge=0,
    )

    departure_time: str | None = None

    centre_name: str = Field(
        ...,
        min_length=2,
    )

    centre_address: str = Field(
        ...,
        min_length=2,
    )

    centre_city: str = Field(
        ...,
        min_length=2,
    )

    centre_latitude: float | None = None

    centre_longitude: float | None = None

    admit_card_data: dict[str, Any] | None = None


# ============================================================
# HELPERS
# ============================================================

def normalize_departure_time(
    departure_time: str | None,
) -> str | None:
    """
    Converts browser datetime-local format:

        2026-08-29T18:00

    into the format expected by the backend:

        2026-08-29 18:00
    """

    if not departure_time:
        return None

    return departure_time.replace("T", " ")


def build_journey_form_data(
    request: JourneyRequest | CompleteExamPlanRequest,
) -> dict[str, Any]:

    return {
        "starting_location": request.starting_location,
        "exam_centre": request.exam_centre,
        "exam_date": request.exam_date,
        "reporting_time": request.reporting_time,
        "gate_closing_time": request.gate_closing_time,

        # RouteService calculates actual travel time.
        "estimated_travel_minutes": 0,

        "local_travel_minutes": (
            request.local_travel_minutes
        ),

        "transport_delay_minutes": (
            request.transport_delay_minutes
        ),

        "departure_time": normalize_departure_time(
            request.departure_time
        ),
    }


def build_centre_input(
    request: CompleteExamPlanRequest,
) -> CentreInput:

    return CentreInput(
        centre_name=request.centre_name,
        address=request.centre_address,
        city=request.centre_city,
        exam_date=request.exam_date,
        reporting_time=request.reporting_time,
        gate_closing_time=request.gate_closing_time,
        latitude=request.centre_latitude,
        longitude=request.centre_longitude,
    )


def build_student_support(
    journey: dict[str, Any],
    centre: Any,
) -> dict[str, Any]:

    # --------------------------------------------------------
    # Safely extract centre support information
    # --------------------------------------------------------

    centre_support = getattr(
        centre,
        "support",
        None,
    )

    if centre_support is None and isinstance(centre, dict):
        centre_support = centre.get(
            "support",
            {},
        )

    if centre_support is None:
        centre_support = {}

    if hasattr(
        centre_support,
        "model_dump",
    ):
        centre_support = centre_support.model_dump()

    recommended_arrival_time = (
        centre_support.get(
            "recommended_arrival_time",
            "06:30",
        )
    )

    checklist = centre_support.get(
        "checklist",
        [
            "Carry the required examination documents.",
            "Carry a valid photo identity document if required by the examination authority.",
            "Keep the examination centre address and route available offline.",
            "Reach the examination area well before the reporting time.",
            "Check the examination instructions before leaving for the centre.",
        ],
    )

    warnings = centre_support.get(
        "warnings",
        [
            "Do not depend on last-minute transportation.",
            "Keep sufficient travel buffer for traffic and unexpected delays.",
            "Verify the examination centre address before starting the journey.",
            "Follow the instructions issued by the official examination authority.",
        ],
    )

    # --------------------------------------------------------
    # Journey values
    # --------------------------------------------------------

    departure_time = journey.get(
        "departure_time",
    )

    expected_arrival = journey.get(
        "expected_arrival",
    )

    exam_date = journey.get(
        "exam_date",
    )

    # --------------------------------------------------------
    # Timeline
    # --------------------------------------------------------

    timeline = []

    if departure_time:
        timeline.append(
            f"{departure_time} - Planned departure"
        )

    if expected_arrival:
        timeline.append(
            f"{expected_arrival} - Expected arrival"
        )

    # These values are supplied separately by the request
    # through the centre information.
    centre_exam_date = None
    reporting_time = None
    gate_closing_time = None

    if isinstance(centre, dict):
        centre_exam_date = centre.get("exam_date")
        reporting_time = centre.get("reporting_time")
        gate_closing_time = centre.get(
            "gate_closing_time"
        )
    else:
        centre_exam_date = getattr(
            centre,
            "exam_date",
            None,
        )

        reporting_time = getattr(
            centre,
            "reporting_time",
            None,
        )

        gate_closing_time = getattr(
            centre,
            "gate_closing_time",
            None,
        )

    if centre_exam_date and reporting_time:
        timeline.append(
            f"{centre_exam_date} {reporting_time} - Official reporting time"
        )

    if centre_exam_date and gate_closing_time:
        timeline.append(
            f"{centre_exam_date} {gate_closing_time} - Gate closing time"
        )

    # --------------------------------------------------------
    # Buffer / risk
    # --------------------------------------------------------

    buffer_minutes = journey.get(
        "buffer_minutes",
        0,
    )

    risk_level = journey.get(
        "risk_level",
        "UNKNOWN",
    )

    if risk_level == "LOW":
        final_message = (
            "Your planned journey reaches the examination "
            "area before the recommended arrival time. "
            "You have a comfortable preparation window."
        )

        journey_warning = (
            "The journey currently has a comfortable "
            "time buffer. Continue with normal preparation "
            "and avoid unnecessary delays."
        )

        delay_action = (
            "If a minor delay occurs, continue monitoring "
            "the journey and maintain the available buffer."
        )

    elif risk_level == "MEDIUM":
        final_message = (
            "Your journey has limited buffer. Keep your "
            "backup transportation option ready and "
            "avoid unnecessary delays."
        )

        journey_warning = (
            "The available travel buffer is limited. "
            "Monitor delays carefully."
        )

        delay_action = (
            "If a delay occurs, immediately consider your "
            "backup transportation option."
        )

    else:
        final_message = (
            "Your journey has a high risk of reaching the "
            "examination area late. Consider leaving earlier "
            "or using a more reliable transportation option."
        )

        journey_warning = (
            "The current journey has insufficient buffer "
            "before the examination schedule."
        )

        delay_action = (
            "If a delay occurs, switch to your backup "
            "transportation option as soon as possible."
        )

    return {
        "exam_date": centre_exam_date or exam_date,

        "leave_time": departure_time,

        "recommended_arrival_time": (
            recommended_arrival_time
        ),

        "preparation_checklist": [
            "Keep all required examination documents ready.",
            "Keep a valid photo identity document if required.",
            "Keep the examination centre address available offline.",
            "Keep your phone sufficiently charged before leaving.",
            "Check the official examination instructions before departure.",
        ],

        "exam_day_timeline": timeline,

        "warnings": [
            journey_warning,
            "The planned journey should be monitored for unexpected delays.",
        ],

        "delay_action": delay_action,

        "backup_guidance": (
            "Keep one backup transportation option ready "
            "and avoid relying on a single last-minute connection."
        ),

        "final_message": final_message,
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Exam Journey Assistant API",
        "status": "running",
        "version": "1.0.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ============================================================
# JOURNEY PLAN
# ============================================================

@app.post("/journey/plan")
def create_plan(
    request: JourneyRequest,
):

    form_data = build_journey_form_data(
        request
    )

    try:

        plan = create_complete_journey_plan(
            form_data=form_data,
            admit_card_data=request.admit_card_data,
        )

        return {
            "success": True,
            "journey": get_journey_summary(
                plan
            ),
        }

    except JourneyServiceError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail="Unable to generate journey plan.",
        ) from exc


# ============================================================
# CENTRE INFORMATION
# ============================================================

@app.post("/centre/info")
def centre_info(
    request: CentreRequest,
):

    centre = CentreInput(
        centre_name=request.centre_name,
        address=request.address,
        city=request.city,
        exam_date=request.exam_date,
        reporting_time=request.reporting_time,
        gate_closing_time=request.gate_closing_time,
        latitude=request.latitude,
        longitude=request.longitude,
    )

    try:

        result = create_centre_result(
            centre
        )

        return {
            "success": True,
            "centre": result,
        }

    except CentreServiceError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail="Unable to generate centre information.",
        ) from exc


# ============================================================
# COMPLETE EXAM PLAN
# ============================================================

@app.post("/exam/complete-plan")
def complete_exam_plan(
    request: CompleteExamPlanRequest,
):

    # --------------------------------------------------------
    # 1. JOURNEY
    # --------------------------------------------------------

    form_data = build_journey_form_data(
        request
    )

    try:

        journey_plan = create_complete_journey_plan(
            form_data=form_data,
            admit_card_data=request.admit_card_data,
        )

        journey_summary = get_journey_summary(
            journey_plan
        )

    except JourneyServiceError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail="Unable to generate journey plan.",
        ) from exc

    # --------------------------------------------------------
    # 2. CENTRE
    # --------------------------------------------------------

    centre_input = build_centre_input(
        request
    )

    try:

        centre_result = create_centre_result(
            centre_input
        )

    except CentreServiceError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail="Unable to generate centre information.",
        ) from exc

    # --------------------------------------------------------
    # Convert centre model to dictionary where possible
    # --------------------------------------------------------

    if hasattr(
        centre_result,
        "model_dump",
    ):
        centre_data = centre_result.model_dump()

    elif hasattr(
        centre_result,
        "dict",
    ):
        centre_data = centre_result.dict()

    elif isinstance(
        centre_result,
        dict,
    ):
        centre_data = centre_result

    else:
        centre_data = {
            "centre_name": request.centre_name,
            "address": request.centre_address,
            "city": request.centre_city,
            "exam_date": request.exam_date,
            "reporting_time": request.reporting_time,
            "gate_closing_time": request.gate_closing_time,
        }

    # --------------------------------------------------------
    # 3. STUDENT SUPPORT
    # --------------------------------------------------------

    student_support = build_student_support(
        journey=journey_summary,
        centre=centre_data,
    )

    # --------------------------------------------------------
    # 4. FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "success": True,

        "exam_plan": {

            "journey": journey_summary,

            "centre": centre_data,

            "student_support": student_support,
        },
    }