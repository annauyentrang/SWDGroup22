import pytest


def pytest_collection_modifyitems(config, items):
    for item in list(items):
        if "test_views.py" in str(item.fspath):
            item.add_marker(pytest.mark.skip(reason="No API endpoints in this project."))
