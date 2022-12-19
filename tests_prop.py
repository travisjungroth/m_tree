from datetime import timedelta
from typing import Any, Iterable

from pytest import fixture
from hypothesis import given, strategies as st, example, settings

from mtree4 import MTree, RouterNode, Node, ValueNode


def get_nodes(node: Any, klass=Node) -> Iterable[RouterNode]:
    if isinstance(node, MTree):
        yield from get_nodes(node.root, klass)
        return
    if isinstance(node, klass):
        yield node
    if isinstance(node, RouterNode):
        for child in node.children:
            yield from get_nodes(child, klass)


def get_nodes_values_and_routers(tree: MTree) -> tuple[set[Node], set[ValueNode], set[RouterNode]]:
    value_nodes, router_nodes = set(), set()
    nodes = set(get_nodes(tree))
    for node in nodes:
        if isinstance(node, ValueNode):
            value_nodes.add(node)
        else:
            router_nodes.add(node)
    return nodes, value_nodes, router_nodes


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
    nodes, value_nodes, router_nodes = get_nodes_values_and_routers(tree)
    parents = {node.parent for node in nodes if node.parent}
    assert parents == router_nodes
    value_parents = {node.parent for node in value_nodes}
    leaves = {node for node in router_nodes if node.is_leaf}
    assert leaves == value_parents
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
    nodes, value_nodes, router_nodes = get_nodes_values_and_routers(tree)
    for value_node in value_nodes:
        for parent in get_parents(value_node):
            assert parent.distance(value_node.value) <= parent.radius


@basic
@settings(max_examples=10000)
def test_perfect_radius(values, cap):
    tree = MTree(values, node_capacity=cap)
    nodes, value_nodes, router_nodes = get_nodes_values_and_routers(tree)
    for router_node in router_nodes:
        max_distance = max(map(router_node.distance, router_node))
        assert router_node.radius == max_distance
