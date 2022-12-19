from typing import Any, Iterable

from pytest import fixture
from hypothesis import given, strategies as st, example

from mtree4 import MTree, RouterNode


def all_router_nodes(tree: MTree) -> Iterable[RouterNode]:
    yield from _all_router_nodes(tree.root)


def _all_router_nodes(node: Any) -> Iterable[RouterNode]:
    if isinstance(node, RouterNode):
        yield node
        for child in node.children:
            yield from _all_router_nodes(child)


@fixture(params=[2, 8], scope='session')
def cap(request):
    return request.param


values_strategy = st.sets(st.text()) | st.sets(st.integers(min_value=0))


def basic(f):
    return given(values=values_strategy, cap=st.integers(2, 8))(f)


@basic
@example(values={''}, cap=2)
def test_tree_basics(values, cap):
    tree = MTree(values, node_capacity=cap)
    assert len(tree) == len(values)
    assert set(tree) == values
    for s in values:
        assert s in tree


@basic
def test_capacity(values, cap):
    tree = MTree([], node_capacity=cap)
    for value in values:
        tree.insert(value)
    for node in all_router_nodes(tree):
        assert len(node.children) <= cap
