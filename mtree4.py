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


class ValueNode(Node[Value]):
    def __repr__(self):
        return f'<{repr(self.router)}>'

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
        return f'<{repr(self.router)}, r={repr(self.radius)}, {repr(self.children)}>'

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
            self.radius = max(self.radius, self.distance(value))
            node = random.choice(self.children)
            node.insert(value)

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
