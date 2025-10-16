from .domain import Volunteer, Event

VOLUNTEERS = [
    Volunteer(
        1,"Allie Nguyen",
        {"Spanish","CPR"},
        {"English","Spanish"},
        {"sat_am","sun_pm"},
        10,
        {"CPR"},
        {"No heavy lifting"}
    ),
    Volunteer(
        2, "Bob Tran",
        {"Driving","Lifting"},
        {"English","Vietnamese"},
        {"sat_am"},
        10,
        set(),
        set()
    ),
]

EVENTS = [
    Event(
        101,
        "Food Pantry Shift",
        {"Lifting"},
        {"English"},
        2,
        {"sat_am"},
        12,
        set()
    ),
    Event(
        102,
        "Health Fair Booth",
        {"CPR"},
        {"English","Spanish"},
        1,
        {"sun_pm"},
        20,
        {"CPR"}
    ),
]
