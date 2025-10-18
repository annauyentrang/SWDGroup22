from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List

class Urgency(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class ParticipationStatus(str, Enum):
    REGISTERED = "Registered"
    ATTENDED = "Attended"
    NO_SHOW = "No-Show"
    CANCELLED = "Cancelled"

@dataclass
class Volunteer:
    id: int
    full_name: str

@dataclass
class ParticipationRecord:
    id: int
    volunteer_id: int
    volunteer_name: str
    event_name: str
    description: str
    location: str
    required_skills: List[str]
    urgency: Urgency
    event_date: date
    capacity_current: int
    capacity_total: int
    languages: List[str]
    status: ParticipationStatus
