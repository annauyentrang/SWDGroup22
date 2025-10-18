from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List, Dict

class Urgency(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class Status(str, Enum):
    REGISTERED = "Registered"
    ATTENDED = "Attended"
    NO_SHOW = "No-Show"
    CANCELLED = "Cancelled"

@dataclass
class Volunteer:
    id: int
    full_name: str

@dataclass
class Participation:
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
    status: Status

VOLUNTEERS: List[Volunteer] = [
    Volunteer(1, "Nareh Hovhanesian"),
    Volunteer(2, "Katia Qahwajian"),
    Volunteer(3, "Simon Zhamkochyan"),
    Volunteer(4, "Angelina Samsonyan"),
]

# The four rows in your screenshot (hard-coded)
PARTICIPATIONS: Dict[int, Participation] = {
    1: Participation(
        id=1, volunteer_id=1, volunteer_name="Nareh Hovhanesian",
        event_name="Park Cleanup",
        description="Neighborhood park litter & brush removal.",
        location="Memorial Park, Houston TX",
        required_skills=["Lifting", "Driving"],
        urgency=Urgency.HIGH,
        event_date=date(2025, 9, 28),
        capacity_current=0, capacity_total=25,
        languages=["English", "Vietnamese"],
        status=Status.REGISTERED
    ),
    2: Participation(
        id=2, volunteer_id=2, volunteer_name="Katia Qahwajian",
        event_name="Blood Donation Desk",
        description="Check-in and refreshments table.",
        location="Community Center, Suite B",
        required_skills=["Customer Service", "Organization"],
        urgency=Urgency.MEDIUM,
        event_date=date(2025, 10, 5),
        capacity_current=12, capacity_total=15,
        languages=["English"],
        status=Status.ATTENDED
    ),
    3: Participation(
        id=3, volunteer_id=3, volunteer_name="Simon Zhamkochyan",
        event_name="Food Drive Sorting",
        description="Sort non-perishables; label and stock shelves.",
        location="St. Mary’s Hall",
        required_skills=["Lifting", "Inventory"],
        urgency=Urgency.LOW,
        event_date=date(2025, 10, 19),
        capacity_current=30, capacity_total=40,
        languages=["English", "Spanish"],
        status=Status.NO_SHOW
    ),
    4: Participation(
        id=4, volunteer_id=4, volunteer_name="Angelina Samsonyan",
        event_name="Shelter Meal Prep",
        description="Prep and package warm meals for families.",
        location="Hope Shelter Kitchen",
        required_skills=["Cooking", "Organization"],
        urgency=Urgency.HIGH,
        event_date=date(2025, 10, 22),
        capacity_current=8, capacity_total=12,
        languages=["English"],
        status=Status.CANCELLED
    ),
}
