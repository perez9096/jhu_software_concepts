from Testing.src.math_functions.summation import summation
import pytest
@pytest.mark.example_mark
def test_sum():
    assert summation(3, 2) == 5

