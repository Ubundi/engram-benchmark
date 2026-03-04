"""Basic import smoke tests."""

from benchmark import run
from benchmark.adapters import get_adapter
from benchmark.tasks import loader
from benchmark.v2 import protocol


def test_import_key_modules() -> None:
    assert run is not None
    assert get_adapter is not None
    assert loader is not None
    assert protocol is not None
