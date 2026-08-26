from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CentreInput:
    centre_name: str
    address: str
    city: str
    exam_date: str
    reporting_time: str
    gate_closing_time: str

    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class CentreSupportInfo:
    recommended_arrival_time: str
    transport_guidance: str
    checklist: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class CentreResult:
    centre_name: str
    address: str
    city: str
    exam_date: str
    reporting_time: str
    gate_closing_time: str
    support: CentreSupportInfo