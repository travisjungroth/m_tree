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
        self.root = []
        for value in values:
            self.insert(value)

    def insert(self, value: Value) -> None:
        self.size += 1
        self.root.append(value)

    def __len__(self) -> int:
        return self.size

    def __contains__(self, item: Value) -> bool:
        return item in self.root

    def __repr__(self):
        return repr(self.root)

    def __iter__(self):
        yield from self.root
