from hypothesis import given, strategies as st

from mtree4 import MTree


@given(st.sets(st.text()))
def test_tree_basics(strings):
    tree = MTree(strings)
    assert len(tree) == len(strings)
    assert set(tree) == strings
    for s in strings:
        assert s in tree
