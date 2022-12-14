from __future__ import annotations

from collections.abc import Iterable
from operator import itemgetter
from typing import Optional, Type, Callable, Protocol, Generic, TypeVar

Value = TypeVar('Value')
Distance = TypeVar('Distance')


def _default_distance(a, b):
    return abs(a - b)


class MTree(Generic[Value, Distance]):
    def __init__(
            self,
            values: Iterable[Value],
            distance: Callable[[Value, Value], Distance] = _default_distance,
            capacity=100,
    ):
        self.distance = distance
        self.capacity = capacity
        self.root: Optional[RouterNode[Value, Distance]] = None
        self.size = 0
        for value in values:
            self.insert(value)

    def insert(self, value: Value) -> None:
        if self.root is None:
            self.root = RouterNode(tree=self, leaf=True, router=value)
        self.root = self.root.insert(value)
        self.size += 1

    def __len__(self) -> int:
        return self.size

    def __contains__(self, item: Value) -> bool:
        return item in self.root

    def __repr__(self):
        return repr(self.root)


    # noinspection PyMethodMayBeStatic
    def promote(self, nodes: list[Node]) -> tuple[Node, Node, list[Node]]:
        return nodes[0], nodes[1], nodes[2:]

    def partition(
            self, a: Node, b: Node, rest: list[Node]
    ) -> tuple[list[Node], list[Node]]:
        a_list, b_list = [a], [b]
        for node in rest:
            if self.distance(a.router, node.router) < self.distance(
                    b.router, node.router
            ):
                a_list.append(node)
            else:
                b_list.append(node)
        return a_list, b_list


class Node(Protocol):
    router: Value
    radius: Distance


class ValueNode(Generic[Value, Distance]):
    radius: Distance = 0

    def __init__(self, router: Value):
        self.router = router

    def __repr__(self):
        return f"<{repr(self.router)}>"

    def __contains__(self, item: Value) -> bool:
        return item == self.router

    def __iter__(self):
        yield self.router



class RouterNode(Generic[Value, Distance]):
    def __init__(
            self, tree: MTree, leaf: bool, router: Value, children: Iterable[Node] = ()
    ):
        self.tree: MTree = tree
        self.leaf: bool = leaf
        self.router: Value = router
        self.radius: Distance = 0
        self.parent: Optional[RouterNode] = None
        self.children: list[Node] = []
        for child in children:
            self._insert_node(child)

    def __repr__(self):
        return f"<{repr(self.router)}:{self.radius}, {[(x.router, x.radius) for x in self.children]}>"

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self):
        yield from self.children

    def __contains__(self, value: Value) -> bool:
        found = any(value in child for child in self.children)
        # if found and self.radius < self.tree.distance(value, self.router):
        #     raise Exception
        return found
        # return any(item in child for child in self.children)

    def x(self, y):
        for a in list(self):
            if self.radius < self.tree.distance(a.router, self.router):
                print(y, a.router, self)
                x = 1
        if self.parent is not None:
            self.parent.x(y)

    def insert(self, value: Value) -> RouterNode:
        if self.leaf:
            node = ValueNode(value)
            self._insert_node(node)
        else:
            distances = [
                (node, self.tree.distance(value, node.router)) for node in self.children
            ]
            node, distance = min(distances, key=itemgetter(1))
            if distance >= node.radius:
                node, distance = min(distances, key=lambda x: x[1] - x[0].radius)
                node.radius = distance
            node.insert(value)
        self.update_radius(node)
        if self.radius < self.tree.distance(value, self.router):
            raise Exception
        self.x(value)
        return self.parent or self

    def update_radius(self, node):
        new_radius = self.tree.distance(node.router, self.router) + node.radius
        self.radius = max(self.radius, new_radius)

    def _insert_node(self, node: Node) -> None:
        if len(self) < self.tree.capacity:
            self.children.append(node)
            node.parent = self
            self.update_radius(node)
        else:
            self._split(node)

    def _split(self, node: Node) -> RouterNode:
        nodes = self.children + [node]
        a, b, rest = self.tree.promote(nodes)
        a_list, b_list = self.tree.partition(a, b, rest)
        self._change_children(router=a.router, nodes=a_list)
        new_node = RouterNode(tree=self.tree, leaf=self.leaf, router=b.router, children=b_list)
        return self._add_to_parent(new_node)

    def _add_to_parent(self, new_node: RouterNode) -> RouterNode:
        if self.parent is None:
            new_root = RouterNode(tree=self.tree, leaf=False, router=self.router, children=[self])
            self.parent = new_root
        self.parent._insert_node(new_node)
        return self.parent

    def _change_children(self, router: Value, nodes: list[Node]) -> None:
        self.router = router
        self.radius = 0
        self.children.clear()
        for node in nodes:
            self._insert_node(node)
