from typing import List, Tuple
from .domain import Volunteer, Event

def score(vol: Volunteer, ev: Event) -> int:
    s = 0
    s += len(vol.skills & ev.required_skills) * 3
    s += len(vol.languages & ev.languages) * 2
    s += 2 if len(vol.availability & ev.time_blocks) else 0
    s += 1 if vol.radius_miles <= ev.max_radius_miles else -5
    if ev.requires - vol.certifications:
        s -= 100  # hard fail
    if "No heavy lifting" in vol.constraints and "Lifting" in ev.required_skills:
        s -= 100  # hard fail
    return s

def match_volunteers(vols: List[Volunteer], ev: Event, k: int=None) -> List[Tuple[Volunteer,int]]:
    ranked = sorted(((v, score(v, ev)) for v in vols), key=lambda x: x[1], reverse=True)
    ranked = [pair for pair in ranked if pair[1] > 0]
    return ranked[: (k or ev.slots)]
