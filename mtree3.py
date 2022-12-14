from __future__ import annotations

import heapq
import random
from collections.abc import Iterable, Sequence
from itertools import chain
from operator import itemgetter
from typing import Optional, Callable, Generic, TypeVar, Union

Value = TypeVar("Value")
Distance = int


def _default_distance(a, b):
    return abs(a - b)


class MTree(Generic[Value]):
    def __init__(
        self,
        values: Iterable[Value],
        distance_fn: Callable[[Value, Value], Distance] = _default_distance,
        capacity=100,
    ):
        self.distance_fn = distance_fn
        self.capacity = capacity
        self.root: Optional[RouterNode[Value, Distance]] = None
        self.size = 0
        for value in values:
            self.insert(value)

    def insert(self, value: Value) -> None:
        if self.root is None:
            self.root = RouterNode(
                children=[ValueNode(value, self)], tree=self, leaf=True
            )
        else:
            self.root = self.root.insert(value)
        self.size += 1

    def __len__(self) -> int:
        return self.size

    def __contains__(self, item: Value) -> bool:
        return item in self.root

    def __repr__(self):
        return repr(self.root)

    def knn(self, Q: Value, k: int) -> list[Value]:
        """
        http://www-db.deis.unibo.it/research/papers/SEBD97.pdf
        """
        k = min(self.size, k)
        # pq for active subtrees. (min distance from Q for all members, Node)
        # min distance is max(0, node.distance(Q) - node.radius)
        PR = [(self.root.min_distance(Q), self.root)]

        # result
        NN = Res(k)

        return NN.items

    def closest(self, value):
        distance, leader = self.root.closest(
            value, self.root.distance(value), self.root
        )
        return leader


class Res:
    def __init__(self, k: int):
        self.k = k
        # negative distance, insertion count, value
        self.items: list[tuple[Distance, int, Value]] = []
        self.count = 0

    def push(self, value: Value, distance: Distance) -> Distance:
        add = -distance, self.count, value
        if len(self.items) < self.k:
            heapq.heappush(self.items, add)
            item = self.items[0]
        else:
            item = heapq.heappushpop(self.items, add)
        self.count += 1
        max_distance = -item[0]
        return max_distance


class Node(Generic[Value]):
    def __init__(self, router: Value, tree: MTree):
        self.router: Value = router
        self.tree: MTree = tree
        self.radius: Distance = 0

    def distance(self, value: Value) -> Distance:
        return self.tree.distance_fn(self.router, value)

    def min_distance(self, value: Value) -> Distance:
        return max(0, self.tree.distance_fn(self.router, value) - self.radius)

    def max_distance(self, value: Value) -> Distance:
        return self.tree.distance_fn(self.router, value) + self.radius


class ValueNode(Node[Value]):
    def __repr__(self):
        return f"<{repr(self.router)}>"

    def __contains__(self, item: Value) -> bool:
        return item == self.router

    def __iter__(self):
        yield self.router


class RouterNode(Node[Value]):
    def __init__(self, children: Sequence[Node], tree: MTree, leaf: bool):
        super().__init__(tree=tree, router=None)
        self.is_leaf: bool = leaf
        self.parent: Optional[RouterNode] = None
        self.radius: Distance = 0
        self.router: Value = None
        self.children: list[Node] = []
        self._set_children(children)

    def __repr__(self):
        return f"<{repr(self.router)}:{self.radius}, {[(x.router, x.radius) for x in self.children]}>"

    def __iter__(self):
        for child in self.children:
            yield from child

    def __contains__(self, value: Value) -> bool:
        distance = self.distance(value)
        return distance == 0 or (
            self.radius >= distance and any(value in child for child in self.children)
        )

    def closest(self, value: Value, distance: Distance, leader: Value) -> tuple[Distance, Value]:
        if self.is_leaf:
            # Rewrite to use min, distance as a key, then just compare
            # to leader.
            x = chain(
                [(x.distance(value), x.router) for x in self.children],
                [(distance, leader)],
            )
            return min(x, key=itemgetter(0))
        for node in self.children:
            if node.distance(value) - node.radius > distance:
                continue
            node: RouterNode
            distance, leader = min(
                (distance, leader), node.closest(value, distance, leader)
            )
        return distance, leader

    def calculate_radius(self, node: Node) -> Distance:
        return max(self.radius, node.max_distance(self.router))

    def insert(self, value: Value) -> RouterNode:
        if self.is_leaf:
            return self._add_child(ValueNode(value, self.tree))

        distances = [(child, child.distance(value)) for child in self.children]
        child, distance = min(distances, key=itemgetter(1))
        if distance >= child.radius:
            child, _ = min(distances, key=lambda x: x[1] - x[0].radius)
        child: RouterNode
        child.insert(value)
        self.radius = self.calculate_radius(child)
        return self.parent or self

    def _add_child(self, node: Node) -> RouterNode:
        self.children.append(node)
        self.radius = self.calculate_radius(node)
        node.parent = self
        if len(self.children) >= self.tree.capacity:
            self._split()
        return self.parent or self

    def _set_children(self, children: Sequence[Node]):
        self.radius = 0
        self.router = children[0].router
        self.children.clear()
        for child in children:
            self._add_child(child)

    def _split(self) -> RouterNode:
        a_list, b_list = self._promote_and_partition()
        new_node = RouterNode(children=b_list, tree=self.tree, leaf=self.is_leaf)
        self._set_children(a_list)
        if self.parent is None:
            self.parent = RouterNode(children=[self], tree=self.tree, leaf=False)
        self.parent._add_child(new_node)
        return self.parent

    def _promote_and_partition(self) -> tuple[Sequence[Value], Sequence[Value]]:
        # could split out promote and partition and make them customizable
        random.shuffle(self.children)
        a, b, *rest = self.children
        a_list, b_list = [a], [b]
        for node in rest:
            if self.distance(a.router) < self.distance(b.router):
                a_list.append(node)
            else:
                b_list.append(node)
        return a_list, b_list
