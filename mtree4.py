from __future__ import annotations

import heapq
import random
from collections import deque
from collections.abc import Iterable, Sequence
from functools import partial, cache
from itertools import chain, combinations, permutations
from operator import itemgetter
from time import sleep
from typing import Optional, Callable, Generic, TypeVar, Union

import editdistance

DEFAULT_NODE_CAPACITY = 8

Value = TypeVar("Value")
Distance = float


def default_distance(a, b):
    return abs(a - b)


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
            node_capacity=DEFAULT_NODE_CAPACITY,
            distance_fn: Callable[[Value, Value], Distance] = default_distance,
    ):
        self.distance_fn = distance_fn
        self.node_capacity = node_capacity
        self.length = 0
        self.root: Union[RouterNode[Value, Distance], tuple] = ()
        for value in values:
            self.insert(value)

    def insert(self, value: Value) -> None:
        self.length += 1
        if isinstance(self.root, tuple):
            self.root = RouterNode(value=value, capacity=self.node_capacity, is_leaf=True)
        else:
            self.root = self.root.insert(value)

    def __len__(self) -> int:
        return self.length

    def __contains__(self, item: Value) -> bool:
        return item in self.root

    def __repr__(self):
        return repr(self.root)

    def __iter__(self) -> Iterable[Value]:
        yield from self.root


class Node(Generic[Value]):
    def __init__(self, value: Value) -> None:
        self.value = value


class ValueNode(Node[Value]):
    def __iter__(self):
        yield self.value

    def __contains__(self, item: Value):
        return item == self.value


class RouterNode(Node[Value]):
    def __init__(self, children=(), *, capacity: int, is_leaf: bool, value: Value=None) -> None:
        if children:
            value = children[0].value
        elif value is not None:
            children = [ValueNode(value)]
        else:
            raise ValueError

        super().__init__(value)
        self.is_leaf = is_leaf
        self.capacity = capacity
        self.parent: Optional[RouterNode] = None

        self.children: list[Node] = []
        self.set_children(children)

    @property
    def is_full(self):
        return len(self.children) >= self.capacity

    def set_children(self, children: Sequence[Node]) -> None:
        self.value = children[0].value
        self.children.clear()
        for child in children:
            self.add_child(child)

    def add_child(self, child: Node):
        if self.is_full:
            raise
        else:
            child.parent = self
            self.children.append(child)

    def insert(self, value: Value) -> RouterNode:
        if self.is_leaf:
            value_node = ValueNode(value)
            if len(self.children) >= self.capacity:
                self.split(value_node)
            else:
                self.add_child(value_node)
        else:
            node = random.choice(self.children)
            node.insert(value)
        return self.parent or self

    def __iter__(self):
        for node in self.children:
            yield from node

    def __contains__(self, item: Value):
        return any(item in node for node in self.children)

    def split(self, node: Node):
        a_list, b_list = self.promote_and_partition(self.children + [node])
        self.set_children(a_list)
        new_node = self.mimic(children=b_list)
        if self.parent is None:
            self.mimic(children=[self, new_node])
        elif len(self.parent.children) < self.capacity:
            self.parent.add_child(new_node)
        else:
            self.parent.split(new_node)

    def mimic(self, children) -> RouterNode:
        return RouterNode(children=children, capacity=self.capacity, is_leaf=self.is_leaf)

    @staticmethod
    def promote_and_partition(candidates: list[Node]):
        random.shuffle(candidates)
        half = len(candidates) // 2
        return candidates[:half], candidates[half:]
