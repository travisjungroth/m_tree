from __future__ import annotations

import heapq
import random
from collections import deque
from collections.abc import Iterable, Sequence
from functools import partial, cache, singledispatch, wraps
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
            self.root = RouterNode(tree=self, value=value, capacity=self.node_capacity, is_leaf=True)
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


def valued(f: Callable[[Node, Value], Distance]) -> Callable[[Union[Value, Node]], Distance]:
    @wraps(f)
    def g(self: Node, value: Union[Value, Node]) -> Distance:
        if isinstance(value, Node):
            value = value.value
        return f(self, value)
    return g


class Node(Generic[Value]):
    def __init__(self, tree: MTree[Value], value: Value) -> None:
        self.tree = tree
        self.value: Value = value
        self.parent: Optional[RouterNode] = None
        self.distance_function = self.tree.distance_function
        self.radius = 0

    @valued
    def distance(self, value: Value) -> Distance:
        return self.distance_function(self.value, value)

    @valued
    def max_distance(self, value: Value) -> Distance:
        return self.distance_function(self.value, value) + self.radius


class ValueNode(Node[Value]):
    def __iter__(self):
        yield self.value

    def __contains__(self, item: Value):
        return item == self.value

    def __repr__(self):
        return f'<{repr(self.value)}>'


class RouterNode(Node[Value]):

    def __init__(self, tree: MTree, children=(), *, capacity: int, is_leaf: bool, value: Value = None) -> None:
        if children:
            value = children[0].value
        elif value is not None:
            children = [ValueNode(tree, value)]
        else:
            raise ValueError

        super().__init__(tree, value)
        self.is_leaf: bool = is_leaf
        self.capacity: int = capacity

        self.children: list[Node] = []
        self.set_children(children)

    def __repr__(self):
        return f'<{repr(self.value)}, r={repr(self.radius)}, {repr(self.children)}>'

    @property
    def is_full(self):
        return len(self.children) >= self.capacity

    def set_children(self, children: Sequence[Node]) -> None:
        self.value = children[0].value
        self.children.clear()
        for child in children:
            self.add_child(child)
        self.radius = max(child.max_distance(self) for child in children)

    def add_child(self, child: Node):
        if self.is_full:
            self.split(child)
        else:
            child.parent = self
            self.children.append(child)
            self.radius = max(self.radius, self.distance(child))

    def insert(self, value: Value) -> RouterNode:
        if self.is_leaf:
            value_node = ValueNode(self.tree, value)
            self.add_child(value_node)
        else:
            self.radius = max(self.radius, self.distance(value))
            node = random.choice(self.children)
            node.insert(value)
        return self.parent or self

    def __iter__(self):
        for node in self.children:
            yield from node

    def __contains__(self, item: Value):
        return any(item in node for node in self.children)

    def __len__(self):
        return len(self.children)

    def split(self, node: Node):
        a_list, b_list = self.promote_and_partition(self.children + [node])
        self.set_children(a_list)
        new_node = self.mimic(children=b_list)
        if self.parent is None:
            self.mimic(children=[self, new_node], is_leaf=False)
        else:
            self.parent.add_child(new_node)

    def mimic(self, *, children, is_leaf=None) -> RouterNode:
        is_leaf = is_leaf if is_leaf is not None else self.is_leaf
        return RouterNode(tree=self.tree, children=children, capacity=self.capacity, is_leaf=is_leaf)

    @staticmethod
    def promote_and_partition(candidates: list[Node]) -> tuple[list[Node], list[Node]]:
        a, b, *nodes = candidates
        a_list, b_list = [a], [b]
        for node in nodes:
            if node.distance(a) < node.distance(b):
                a_list.append(node)
            else:
                b_list.append(node)
        return a_list, b_list
