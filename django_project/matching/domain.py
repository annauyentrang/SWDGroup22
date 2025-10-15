from dataclasses import dataclass, field
from typing import List, Set

@dataclass(frozen=True)
class Volunteer:
    id: int
    name: str
    skills: Set[str]
    languages: Set[str]
    availability: Set[str]   # e.g., {"sat_am","sun_pm"}
    radius_miles: int
    certifications: Set[str] = field(default_factory=set)
    constraints: Set[str] = field(default_factory=set)

@dataclass(frozen=True)
class Event:
    id: int
    title: str
    required_skills: Set[str]
    languages: Set[str]
    slots: int
    time_blocks: Set[str]     # e.g., {"sat_am"}
    max_radius_miles: int
    requires: Set[str] = field(default_factory=set)
