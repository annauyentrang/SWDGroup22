from typing import Iterable
from datetime import date
MAX_LEN_SHORT = 120
MAX_LEN_LONG = 500

def require(value, field):
    if value in (None, ""):
        raise ValueError(f"{field} is required")

def max_len(value: str, limit: int, field: str):
    if value and len(value) > limit:
        raise ValueError(f"{field} must be ≤ {limit} characters")

def non_negative_int(n, field: str):
    if not isinstance(n, int) or n < 0:
        raise ValueError(f"{field} must be a non-negative integer")

def positive_int(n, field: str):
    if not isinstance(n, int) or n <= 0:
        raise ValueError(f"{field} must be a positive integer")

def list_of_strings(xs: Iterable, field: str):
    if xs is None:
        raise ValueError(f"{field} is required")
    if not isinstance(xs, Iterable) or isinstance(xs, (str, bytes)):
        raise ValueError(f"{field} must be a list of strings")
    ok = False
    for x in xs:
        ok = True
        if not isinstance(x, str) or not x.strip():
            raise ValueError(f"{field} contains an invalid item")
    if not ok:
        raise ValueError(f"{field} must not be empty")

def capacity_ok(current: int, total: int):
    if current > total:
        raise ValueError("capacity_current cannot exceed capacity_total")
def date_in_range(d: date, start: date | None, end: date | None) -> bool:
    if start and d < start:
        return False
    if end and d > end:
        return False
    return True