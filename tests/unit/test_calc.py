
from backend.calculations import calculate_ebit


def test_calculate_ebit_basic():
    assert calculate_ebit(100000, 60000) == 40000


def test_calculate_ebit_with_utlegg():
    assert calculate_ebit(100000, 60000, 5000) == 35000


def test_calculate_ebit_zero():
    assert calculate_ebit(0, 0, 0) == 0
