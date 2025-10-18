import pytest
from volunteers_r_us.history.validators import capacity_ok, list_of_strings, max_len

def test_capacity_ok():
    capacity_ok(0, 1)
    with pytest.raises(ValueError):
        capacity_ok(2, 1)

def test_list_of_strings():
    list_of_strings(["a", "b"], "skills")
    with pytest.raises(ValueError):
        list_of_strings([], "skills")
    with pytest.raises(ValueError):
        list_of_strings([1, 2], "skills")

def test_max_len():
    max_len("abc", 3, "f")
    with pytest.raises(ValueError):
        max_len("abcd", 3, "f")
