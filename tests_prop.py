from itertools import chain
from typing import Any, Iterable

from hypothesis import given, strategies as st
from pytest import mark

from mtree4 import MTree, RouterNode, Node, LeafNode


def get_nodes(node: Any, klass=Node) -> Iterable[RouterNode]:
    if isinstance(node, MTree):
        yield from get_nodes(node.root, klass)
        return
    if isinstance(node, klass):
        yield node
    if isinstance(node, RouterNode):
        for child in node.children:
            yield from get_nodes(child, klass)


def get_nodes_leaves_and_routers(tree: MTree) -> tuple[set[Node], set[LeafNode], set[RouterNode]]:
    leaf_nodes, router_nodes = set(), set()
    nodes = set(get_nodes(tree))
    for node in nodes:
        if isinstance(node, LeafNode):
            leaf_nodes.add(node)
        else:
            router_nodes.add(node)
    return nodes, leaf_nodes, router_nodes


def get_parents(node: Node) -> Iterable[RouterNode]:
    if node.parent is not None:
        yield node.parent
        yield from get_parents(node.parent)


values_strategy = st.sets(st.text()) | st.sets(st.integers(min_value=0))


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
    for node in get_nodes(tree, RouterNode):
        assert len(node.children) <= cap


@basic
def test_parents(values, cap):
    tree = MTree(values, node_capacity=cap)
    nodes, leaf_nodes, router_nodes = get_nodes_leaves_and_routers(tree)
    parents = {node.parent for node in nodes if node.parent is not None}
    assert parents == router_nodes
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
    nodes, leaf_nodes, router_nodes = get_nodes_leaves_and_routers(tree)
    for leaf_node in leaf_nodes:
        for child in leaf_node.children:
            for node in chain(get_parents(leaf_node), [leaf_node]):
                assert node.distance(child) <= node.radius
