from functools import partial
from heapq import nsmallest
from random import randint
from typing import Any, Iterable

from hypothesis import given, strategies as st, settings

from m_tree.classes import MTree, Node, ParentNode, DistanceFunction


def get_nodes(node: Any, klass=Node) -> Iterable[ParentNode]:
    if isinstance(node, MTree):
        yield from get_nodes(node.root, klass)
        return
    if isinstance(node, klass):
        yield node
    if isinstance(node, ParentNode):
        for child in node.children:
            yield from get_nodes(child, klass)


values_strategy = st.sets(st.integers(min_value=0)) | st.sets(st.text())


def basic(f):
    return given(values=values_strategy, cap=st.integers(2, 4))(f)


@basic
def test_tree_basics(values, cap):
    tree = MTree(values, node_capacity=cap)
    assert len(tree) == len(values)
    assert set(tree) == values
    for s in values:
        assert s in tree


@basic
def test_capacity(values, cap):
    tree = MTree(node_capacity=cap)
    for value in values:
        tree.insert(value)
    for node in get_nodes(tree, ParentNode):
        assert len(node.children) <= cap


@basic
def test_parents(values, cap):
    tree = MTree(values, node_capacity=cap)
    nodes = set(get_nodes(tree.root))
    parent_nodes = {node for node in nodes if isinstance(node, ParentNode)}
    parents = {node.parent for node in nodes if node.parent is not None}
    assert parents == parent_nodes
    for node in nodes:
        if node.parent is None:
            continue
        assert node in node.parent.children
    for parent in parents:
        for child in parent.children:
            assert child.parent is parent


@basic
def test_sufficient_radius(values, cap):
    tree = MTree(values, node_capacity=cap)
    for node in get_nodes(tree.root, ParentNode):
        for value in node:
            assert node.distance(value) <= node.radius


vectors = st.tuples(st.integers(), st.integers())


class TestKnn:
    @given(st.sets(vectors, min_size=1), vectors, st.integers(1))
    def test_correct(self, values, needle, k):
        tree = MTree(values)
        res = tree.knn(needle, k)
        needle_distance = partial(tree.distance_function, needle)
        assert len(res) == min(k, len(values))
        res = sorted(res, key=needle_distance)
        x = nsmallest(k, values, key=needle_distance)
        actual_furthest = max(x, key=needle_distance)
        assert needle_distance(res[-1]) == needle_distance(actual_furthest)

    def test_efficient(self):
        searches = 10
        size = 10**4

        def vector():
            dim = 3
            space = 10**10
            return tuple(randint(0, space) for _ in range(dim))

        values = {(vector()) for _ in range(size)}
        k = 4
        tree = MTree(values, distance_function=DistanceFunction(), node_capacity=8)

        print()
        for _ in range(searches):
            needle = vector()
            tree.distance_function.reset_counter()
            assert not tree.distance_function.call_count
            tree.knn(needle, k)
            assert tree.distance_function.call_count < len(values)
            print(tree.distance_function.call_count, len(values))
