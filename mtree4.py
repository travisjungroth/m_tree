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
            values: Iterable[Value],
            distance_fn: Callable[[Value, Value], Distance] = default_distance,
    ):
        self.distance_fn = distance_fn
        self.size = 0
        self.root: Union[RouterNode[Value, Distance], tuple] = ()
        for value in values:
            self.insert(value)

    def insert(self, value: Value) -> None:
        self.size += 1
        if isinstance(self.root, tuple):
            value = ValueNode(value)
            self.root = RouterNode(children=[value])
        else:
            self.root.insert(value)

    def __len__(self) -> int:
        return self.size

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
    # def __contains__(self, value: Value) -> bool:
    #     return value == s
    def __iter__(self):
        yield self.value

    def __contains__(self, item: Value):
        return item == self.value


class RouterNode(Node[Value]):
    def __init__(self, children: Sequence[Node], value: Optional[Value] = None) -> None:
        value = value if value is not None else children[0].value
        super().__init__(value)
        self.children = list(children)

    def insert(self, value: Value):
        self.children.append(ValueNode(value))

    def __iter__(self):
        for node in self.children:
            yield from node

    def __contains__(self, item: Value):
        return any(item in node for node in self.children)
