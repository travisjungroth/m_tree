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
Distance = Union[float, int]


@singledispatch
def default_distance(a, b):
    return abs(a - b)


@default_distance.register
def _(a: str, b: str):
    return editdistance.eval(a, b)


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
        self.root: Union[RouterNode[Value, Distance], tuple] = ()
        for value in values:
            self.insert(value)

    def insert(self, value: Value) -> None:
        self.length += 1
        if isinstance(self.root, tuple):
            self.root = LeafNode(tree=self, children=[value])
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


Child = TypeVar('Child')


class Node(Generic[Value, Child]):
    def __init__(self, tree: MTree[Value], children: Sequence[Child]) -> None:
        self.tree = tree
        self.parent: Optional[RouterNode] = None
        self.distance_function = self.tree.distance_function
        self.children = []
        self.capacity = self.tree.node_capacity
        self.router = None
        self.radius = 0
        self.set_children(children)

    @staticmethod
    def unwrap(item):
        if isinstance(item, Node):
            return item.router
        return item

    def distance_between(self, a: Child, b: Child):
        return self.distance_function(self.unwrap(a), self.unwrap(b))

    def distance(self, item):
        if isinstance(item, Node):
            return self.distance_function(self.router, item.router) + item.radius
        return self.distance_function(self.router, item)

    def __repr__(self):
        return f'<{repr(self.router)}, r={repr(self.radius)}, {repr(self.children)}>'

    @property
    def is_full(self):
        return len(self.children) >= self.capacity

    def set_children(self, children: Sequence[Node]) -> None:
        self.router = children[0].router if isinstance(children[0], Node) else children[0]
        self.children.clear()
        for child in children:
            self._add_child(child)
        self.radius = max(self.distance(child) for child in children)

    def add_child(self, child):
        if self.is_full:
            self.split(child)
        else:
            self._add_child(child)

    def _add_child(self, child):
        self.children.append(child)
        self.radius = max(self.radius, self.distance(child))

    def insert(self, value: Value) -> None:
        raise NotImplementedError

    def __len__(self):
        return len(self.children)

    def split(self, node: Node):
        a_list, b_list = self.promote_and_partition(self.children + [node])
        self.set_children(a_list)
        new_node = self.__class__(tree=self.tree, children=b_list)
        if self.parent is None:
            self.parent = RouterNode(tree=self.tree, children=[self, new_node])
        else:
            self.parent.add_child(new_node)

    def promote_and_partition(self, candidates: list) -> tuple[list, list]:
        a, b, *items = candidates
        a_list, b_list = [a], [b]
        for item in items:
            if self.distance_between(a, item) < self.distance_between(b, item):
                a_list.append(item)
            else:
                b_list.append(item)
        return a_list, b_list


class RouterNode(Node[Value, Node]):
    def insert(self, value: Value) -> None:
        self.radius = max(self.radius, self.distance(value))
        node = random.choice(self.children)
        node.insert(value)

    def _add_child(self, child: Node):
        super()._add_child(child)
        child.parent = self

    def __iter__(self) -> Iterable[Value]:
        for node in self.children:
            yield from node

    def __contains__(self, item: Value):
        return any(item in node for node in self.children)


class LeafNode(Node[Value, Value]):
    def __iter__(self) -> Iterable[Value]:
        yield from self.children

    def __contains__(self, item: Value):
        return item in self.children

    def insert(self, value: Value) -> None:
        self.add_child(value)


