from __future__ import annotations

import heapq
from functools import cache
from itertools import zip_longest
from typing import Generic, Iterable, TypeVar, Union, Callable

import editdistance

Item = TypeVar("Item")
Value = TypeVar("Value")
Distance = Union[int, float]
Comparable = Distance


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

    def __iter__(self) -> Iterable[Item]:
        return (item[2] for item in self.pq if item[2] in self.items)


def default_distance(a, b):
    if isinstance(a, str):
        return editdistance.eval(a, b)
    if isinstance(a, tuple):
        return sum(abs(x - y) for x, y in zip_longest(a, b, fillvalue=0))
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
