from dataclasses import dataclass, field


@dataclass
class SupportInput:
    exam_date: str
    reporting_time: str
    gate_closing_time: str

    risk_level: str
    buffer_minutes: int

    expected_arrival: str
    departure_time: str

    previous_day_recommended: bool = False
    same_day_travel: bool = True


@dataclass
class SupportResult:
    exam_date: str

    leave_time: str
    recommended_arrival_time: str

    preparation_checklist: list[str] = field(default_factory=list)
    exam_day_timeline: list[str] = field(default_factory=list)

    warnings: list[str] = field(default_factory=list)
    delay_action: str = ""

    backup_guidance: str = ""

    final_message: str = ""