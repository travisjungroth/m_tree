from hypothesis import given, strategies as st

from mtree4 import MTree


@given(st.sets(st.text()))
def test_contains(strings):
    tree = MTree(strings)
    assert set(tree) == strings
