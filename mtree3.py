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
Distance = int


slow = set()
counter = [0]

def _default_distance(a, b):
    if hash(a) > hash(b):
        a, b = b, a
    return _f(a, b)

@cache
def _f(a, b):
    counter[0] += 1
    return editdistance.eval(a, b)

# @cache
# def u(s):
#     return sum(ord(c) * i for i, c in enumerate(s, start=1))


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
            self.root.insert(value)
        self.size += 1

    def __len__(self) -> int:
        return self.size

    def __contains__(self, item: Value) -> bool:
        return item in self.root

    def __repr__(self):
        return repr(self.root)

    def __iter__(self):
        yield from self.root

    def knn(self, value: Value, k: int) -> list[Value]:
        """
        http://www-db.deis.unibo.it/research/papers/SEBD97.pdf
        """
        if k >= self.size:
            return sorted(self, key=partial(self.distance_fn, value))
        results = _KNNResults(k)
        pq = PriorityQueue()
        pq.push(self.root.min_distance(value), self.root)
        while pq:
            node: RouterNode
            min_distance_q, node = pq.pop()
            results.discard(node)
            if min_distance_q > results.max_distance():
                break
            for child_node in node.children:
                if abs(node.distance(value) - node.distance(child_node.router)) - child_node.radius <= results.max_distance():
                    if child_node.min_distance(value) <= results.max_distance():
                        if isinstance(child_node, RouterNode):
                            pq.push(child_node.min_distance(value), child_node)
                        results.push(child_node.max_distance(value), child_node)
        return results.values()

    def closest(self, value: Value) -> Value:
        distance, leader = self.root.closest(
            value, self.root.distance(value), self.root
        )
        return leader

    def closest_iter2(self, value: Value) -> Value:
        max_distance = float('inf')
        q = deque([self.root])
        closest_value = self.root.router
        while q:
            parent_node = q.pop()
            if parent_node.min_distance(value) >= max_distance:
                continue
            for node in parent_node.children:
                if isinstance(node, RouterNode):
                    q.appendleft(node)
                child_max = node.max_distance(value)
                if child_max < max_distance:
                    max_distance = child_max
                    closest_value = node.router
        return closest_value


class PriorityQueue:
    def __init__(self) -> None:
        self.items: list[tuple[Distance, int, Node]] = []
        self.count = 0  # incrementing tie-breaker for comparisons

    def __bool__(self):
        return bool(self.items)

    def push(self, distance: Distance, node: Node) -> None:
        new = distance, self.count, node
        heapq.heappush(self.items, new)
        self.count += 1

    def pop(self) -> tuple[Distance, Node]:
        priority, count, value = heapq.heappop(self.items)
        return priority, value


class _KNNResults:
    def __init__(self, k: int) -> None:
        self.pq: list[tuple[Distance, int, Node]] = []
        self.count = 0  # incrementing tie-breaker for comparisons
        self.k = k
        self.set: set[Node] = set()

    def __len__(self):
        return len(self.set)

    def push(self, distance: Distance, node: Node) -> None:
        """
        Assumes node not in queue
        """
        if distance > self.max_distance():
            return
        item = -distance, self.count, node
        self.count += 1
        self.set.add(node)
        heapq.heappush(self.pq, item)
        if len(self) > self.k:
            self.pop()

    def pop(self):
        self.clear()
        _, _, node = heapq.heappop(self.pq)
        self.set.remove(node)
        self.clear()

    def clear(self):
        if not self.pq:
            return
        while self.pq[0][2] not in self.set:
            heapq.heappop(self.pq)

    def discard(self, node: Node) -> None:
        self.set.discard(node)

    def max_distance(self) -> Distance:
        return -self.pq[0][0] if self.pq else float('inf')

    def values(self) -> list:
        return [item[2].router for item in self.pq if isinstance(item[2], ValueNode)]


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
        # return f"<{hash(self.router)}>"
        # return f"<{repr(self.router)}>"
        return str(id(self))

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
        self.router: Value = children[0].router
        self.children: list[Node] = []
        for child in children:
            self.children.append(child)
            self.radius = max(self.radius, child.max_distance(self.router))
            child.parent = self

    def __hash__(self):
        return hash(id(self))

    def __repr__(self):
        # return f"<{repr(self.router)}:{self.radius}, {[(x.router, x.radius) for x in self.children]}>"
        # return f"<{hash(self.router)}:{self.radius}, {[(hash(x.router), x.radius) for x in self.children]}>"
        return f"<{str(id(self.router))}:{self.radius}, {[(str(id(x.router)), x.radius) for x in self.children]}>"


    def __iter__(self):
        for child in self.children:
            yield from child

    def __contains__(self, value: Value) -> bool:
        distance = self.distance(value)
        return distance == 0 or (
                self.radius >= distance and any(value in child for child in self.children)
        )

    def calculate_radius(self, node: Node) -> Distance:
        return max(self.radius, node.max_distance(self.router))

    def insert(self, value: Value, parent: Optional[Node] = None):
        if self.is_leaf:
            self.add_node(ValueNode(value, self.tree))
        else:
            # distances = [(child, child.distance(value)) for child in self.children]
            # child, distance = min(distances, key=itemgetter(1))
            # if distance >= child.radius:
            #     child, _ = min(distances, key=lambda x: x[1] - x[0].radius)
            # child: RouterNode
            child = random.choice(self.children)
            child.insert(value)
        self.radius = max(self.radius, self.distance(value))

    def add_node(self, node: Node):
        node.parent = self
        if len(self.children) <= self.tree.capacity:
            self.children.append(node)
            self.radius = max(self.radius, node.max_distance(self.router))
            return
        a_list, b_list = self._promote_and_partition()
        self.radius = 0
        self.children.clear()
        self.router = a_list[0].router
        for a_child in a_list:
            self.children.append(a_child)
            self.radius = max(self.radius, node.max_distance(self.router))
            a_child.parent = self

        b_node = RouterNode(children=b_list, tree=self.tree, leaf=self.is_leaf)
        if self is self.tree.root:
            self.parent = RouterNode(children=[self], tree=self.tree, leaf=False)
            self.tree.root = self.parent
        self.parent.add_node(b_node)
        self.parent.radius = max(self.parent.radius, self.max_distance(self.parent.router))

    def _promote_and_partition(self) -> tuple[Sequence[Value], Sequence[Value]]:
        # a, b = max(permutations(self.children, r=2), key=lambda x: self.tree.distance_fn(x[0].router, x[1].router))
        # a_list, b_list = [], []
        # nodes = self.children

        # random.shuffle(self.children)
        a, b, *nodes = self.children
        a_list, b_list = [a], [b]

        for node in nodes:
            if random.random() < 0.5:
            # if node.distance(a.router) < node.distance(b.router):
                a_list.append(node)
            else:
                b_list.append(node)

        # for l in [a_list, b_list]:
        #     router = min(l, key=lambda x: sum([y.max_distance(x.router) for y in l]))
        #     i = l.index(router)
        #     l[0], l[i] = l[i], l[0]
        return a_list, b_list
