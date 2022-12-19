from __future__ import annotations

import heapq
import random
from collections import deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from functools import partial, cache, singledispatch, wraps, singledispatchmethod
from itertools import chain, combinations, permutations
from operator import itemgetter
from time import sleep
from typing import Optional, Callable, Generic, TypeVar, Union

import editdistance

DEFAULT_NODE_CAPACITY = 8

Value = TypeVar("Value")
Distance = Union[int, float]
Comparable = Distance
Item = TypeVar("Item")


@singledispatch
def default_distance(a, b):
    return abs(a - b)


@default_distance.register
def _(a: str, b: str):
    return editdistance.eval(a, b)


class PriorityQueue(Generic[Item]):
    def __init__(self) -> None:
        self.items: list[tuple[Comparable, int, Item]] = []
        self.count = 0  # incrementing tie-breaker for comparisons

    def __bool__(self):
        return bool(self.items)

    def push(self, priority: Comparable, item: Item) -> None:
        new = priority, self.count, item
        heapq.heappush(self.items, new)
        self.count += 1

    def pop(self) -> tuple[Comparable, Item]:
        priority, count, item = heapq.heappop(self.items)
        return priority, item


class LimitedSet(Generic[Item]):
    def __init__(self, k: int) -> None:
        self.pq: list[tuple[Comparable, int, Item]] = []
        self.count = 0  # incrementing tie-breaker for comparisons
        self.k = k
        self.items: set[Item] = set()

    def add(self, priority: Comparable, item: Item) -> None:
        if priority > self.limit():
            return
        self.items.add(item)
        entry = -priority, self.count, item
        heapq.heappush(self.pq, entry)
        if len(self.items) > self.k:
            _, _, item = heapq.heappop(self.pq)
            self.items.remove(item)
        self.count += 1

    def discard(self, item: Item) -> None:
        self.items.discard(item)

    def limit(self):
        while self.pq and self.pq[0][2] not in self.items:
            heapq.heappop(self.pq)
        return float("inf") if len(self.items) < self.k else -self.pq[0][0]

    def sorted(self) -> list[Item]:
        return [item[2] for item in sorted(self.pq, reverse=True) if item[2] in self.items]


class DistanceFunction:
    def __init__(self, fn: Callable = default_distance) -> None:
        self.fn = cache(fn)
        self.calls = set()

    def __call__(self, a, b):
        if a > b:
            a, b = b, a
        self.calls.add((a, b))
        return self.fn(a, b)

    def reset_counter(self):
        self.calls.clear()

    @property
    def call_count(self):
        return len(self.calls)


class MTree(Generic[Value]):
    def __init__(
        self,
        values: Iterable[Value] = (),
        *,
        node_capacity=DEFAULT_NODE_CAPACITY,
        distance_function: Callable[[Value, Value], Distance] = default_distance,
    ):
        self.distance_function = distance_function
        self.node_capacity = node_capacity
        self.length = 0
        self.root: Union[ParentNode[Value], tuple] = ()
        for value in values:
            self.insert(value)

    def insert(self, value: Value) -> None:
        self.length += 1
        if isinstance(self.root, tuple):
            self.root = ParentNode(tree=self, children=[ValueNode(self, value)])
        else:
            self.root.insert(value)
            self.root = self.root.parent or self.root

    def __len__(self) -> int:
        return self.length

    def __contains__(self, item: Value) -> bool:
        return item in self.root

    def __repr__(self):
        return repr(self.root)

    def __iter__(self) -> Iterable[Value]:
        yield from self.root

    def knn(self, value: Value, k: int) -> list[Value]:
        assert k >= 0
        if not k:
            return []
        if k >= self.length:
            return sorted(self, key=partial(self.distance_function, value))
        results = LimitedSet(k)
        pq = PriorityQueue()
        pq.push(self.root.min_distance(value), self.root)
        while pq:
            node: ParentNode
            min_distance_q, node = pq.pop()
            results.discard(node)
            for child_node in node.children:
                # if abs(node.distance(value) - node.distance(child_node.router)) - child_node.radius <= results.limit():
                #     if child_node.min_distance(value) <= results.limit():
                        if isinstance(child_node, ParentNode):
                            pq.push(child_node.min_distance(value), child_node)
                        results.add(child_node.max_distance(value), child_node)
        return [node.router for node in results.sorted()]


class Node(Generic[Value]):
    def __init__(self, tree: MTree[Value], router=Value) -> None:
        self.tree = tree
        self.distance_function = self.tree.distance_function
        self.router = router
        self.parent = None
        self.radius = 0

    def distance(self, item: Union[Node, Value]) -> Distance:
        if isinstance(item, Node):
            return self.distance_function(self.router, item.router) + item.radius
        return self.distance_function(self.router, item)

    def min_distance(self, value: Value) -> Distance:
        return max(0, self.distance_function(self.router, value) - self.radius)

    def max_distance(self, value: Value) -> Distance:
        return self.distance_function(self.router, value) + self.radius


class ValueNode(Node[Value]):
    def __repr__(self):
        return f"<{repr(self.router)}>"

    def __iter__(self):
        yield self.router

    def __contains__(self, item):
        return item == self.router


class ParentNode(Node[Value]):
    def __init__(self, tree: MTree[Value], children: Sequence[Node]) -> None:
        super().__init__(tree=tree, router=None)
        self.parent: Optional[ParentNode[Value]] = None
        self.radius = 0
        self.children: list[Node] = []
        self.capacity = self.tree.node_capacity
        self.set_children(children)

    def __repr__(self):
        return f"<{repr(self.router)}, r={repr(self.radius)}, {repr(self.children)}>"

    def set_children(self, children: Sequence[Node]) -> None:
        self.router = children[0].router
        self.children.clear()
        for child in children:
            self._add_child(child)
        self.radius = max(self.distance(child) for child in children)

    def add_child(self, child: Node):
        if len(self.children) >= self.capacity:
            self.split(child)
        else:
            self._add_child(child)

    def _add_child(self, child: Node):
        child.parent = self
        self.children.append(child)
        self.radius = max(self.radius, self.distance(child))

    def insert(self, value: Value) -> None:
        if isinstance(self.children[0], ValueNode):
            self.add_child(ValueNode(self.tree, value))
        else:
            self.children: list[ParentNode]
            self.radius = max(self.radius, self.distance(value))
            node = min(self.children, key=lambda x: x.distance(value))
            if not node.covers(value):
                node = min(self.children, key=lambda x: x.increase_required(value))
            node.insert(value)

    def covers(self, value: Value) -> bool:
        return self.distance(value) <= self.radius

    def increase_required(self, value: Value):
        return self.distance(value) - self.radius

    def __len__(self):
        return len(self.children)

    def split(self, node: Node):
        a_list, b_list = self.promote_and_partition(self.children + [node])
        self.set_children(a_list)
        new_node = self.__class__(tree=self.tree, children=b_list)
        if self.parent is None:
            self.parent = ParentNode(tree=self.tree, children=[self, new_node])
        else:
            self.parent.add_child(new_node)

    def promote_and_partition(self, candidates: list) -> tuple[list, list]:
        a, b, *items = candidates
        a_list, b_list = [a], [b]
        for item in items:
            if a.distance(item) < b.distance(item):
                a_list.append(item)
            else:
                b_list.append(item)
        return a_list, b_list

    def __iter__(self) -> Iterable[Value]:
        for node in self.children:
            yield from node

    def __contains__(self, item: Value) -> bool:
        return any(item in node for node in self.children)
