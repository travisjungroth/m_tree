from itertools import chain
from typing import Any, Iterable

from hypothesis import given, strategies as st
from pytest import mark

from mtree4 import MTree, Node, ParentNode


def get_nodes(node: Any, klass=Node) -> Iterable[ParentNode]:
    if isinstance(node, MTree):
        yield from get_nodes(node.root, klass)
        return
    if isinstance(node, klass):
        yield node
    if isinstance(node, ParentNode):
        for child in node.children:
            yield from get_nodes(child, klass)


# def get_nodes_leaves_and_routers(tree: MTree) -> tuple[set[Node], set[LeafNode], set[RouterNode]]:
#     leaf_nodes, router_nodes = set(), set()
#     nodes = set(get_nodes(tree))
#     for node in nodes:
#         if isinstance(node, LeafNode):
#             leaf_nodes.add(node)
#         else:
#             router_nodes.add(node)
#     return nodes, leaf_nodes, router_nodes


# def get_parents(node: ParentNode) -> Iterable[RouterNode]:
#     if node.parent is not None:
#         yield node.parent
#         yield from get_parents(node.parent)


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
    nodes = get_nodes(tree.root, ParentNode)
    for node in nodes:
        for value in node:
            assert node.distance(value) <= node.radius
