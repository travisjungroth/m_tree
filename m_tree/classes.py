from __future__ import annotations

from itertools import chain
from typing import (
    Collection,
    Iterable,
    Union,
    Callable,
    Iterator,
    Generic,
    Sequence,
    Optional,
)

from m_tree.helpers import (
    Value,
    Distance,
    DistanceFunction,
    default_distance,
    LimitedSet,
    PriorityQueue,
)

DEFAULT_NODE_CAPACITY = 8


class MTree(Collection[Value]):
    def __init__(
        self,
        values: Iterable[Value] = (),
        *,
        node_capacity=DEFAULT_NODE_CAPACITY,
        distance_function: Union[
            Callable[[Value, Value], Distance], DistanceFunction
        ] = default_distance,
    ):
        """
        Initialize the MTree.

        :param values: An iterable of values to be inserted into the MTree.
        :param node_capacity: Capacity of the nodes in the MTree.
        :param distance_function: A function to calculate the distance between two values.
        """
        self.distance_function = distance_function
        self.node_capacity = node_capacity
        self.length = 0
        self.root: Union[ParentNode[Value], tuple] = ()
        for value in values:
            self.insert(value)

    def insert(self, value: Value) -> None:
        """
        Insert a value into the MTree.

        :param value: The value to be inserted.
        """
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

    def __repr__(self) -> str:
        return repr(self.root)

    def __iter__(self) -> Iterator[Value]:
        yield from self.root

    def knn(self, value: Value, k: int) -> list[Value]:
        """
        Find the k nearest neighbors of the given value in the MTree.

        :param value: The value for which to find the nearest neighbors.
        :param k: The number of nearest neighbors to find.
        :return: A list of the k nearest neighbor values.
        """
        assert k >= 0
        if not k:
            return []
        if k >= self.length:
            return list(self)
        results = LimitedSet(k)
        pq = PriorityQueue()
        pq.push(self.root.min_distance(value), self.root)
        while pq:
            node: ParentNode
            min_distance_q, node = pq.pop()
            results.discard(node)
            for child_node in node.children:
                if (
                    abs(node.distance(value) - node.distance(child_node.router))
                    - child_node.radius
                    <= results.limit()
                ):
                    if child_node.min_distance(value) <= results.limit():
                        if isinstance(child_node, ParentNode):
                            pq.push(child_node.min_distance(value), child_node)
                        results.add(child_node.max_distance(value), child_node)
        return [node.router for node in results]


class Node(Generic[Value]):
    def __init__(self, tree: MTree[Value], router=Value) -> None:
        """
        Initialize the base Node class.

        :param tree: The MTree instance this node belongs to.
        :param router: The router value of the node.
        """
        self.tree = tree
        self.distance_function = self.tree.distance_function
        self.router = router
        self.parent = None
        self.radius = 0

    def distance(self, item: Union[Node, Value]) -> Distance:
        """
        Calculate the distance from this node to another node or value.

        :param item: The other node or value to calculate the distance to.
        :return: The calculated distance.
        """
        if isinstance(item, Node):
            return self.distance_function(self.router, item.router) + item.radius
        return self.distance_function(self.router, item)

    def min_distance(self, value: Value) -> Distance:
        """
        Calculate the minimum distance from this node to a value.

        :param value: The value to calculate the minimum distance to.
        :return: The calculated minimum distance.
        """
        return max(0, self.distance_function(self.router, value) - self.radius)

    def max_distance(self, value: Value) -> Distance:
        """
        Calculate the maximum distance from this node to a value.

        :param value: The value to calculate the maximum distance to.
        :return: The calculated maximum distance.
        """
        return self.distance_function(self.router, value) + self.radius


class ValueNode(Node[Value]):
    def __repr__(self) -> str:
        return f"<{repr(self.router)}>"

    def __iter__(self) -> Iterator[Value]:
        yield self.router

    def __contains__(self, item) -> bool:
        return item == self.router


class ParentNode(Node[Value]):
    def __init__(self, tree: MTree[Value], children: Sequence[Node]) -> None:
        """
        Initialize the ParentNode class.

        :param tree: The MTree instance this parent node belongs to.
        :param children: A sequence of child nodes for this parent node.
        """
        super().__init__(tree=tree, router=None)
        self.parent: Optional[ParentNode[Value]] = None
        self.radius = 0
        self.children: list[Node] = []
        self.capacity = self.tree.node_capacity
        self.set_children(children)

    def __repr__(self):
        return f"<{repr(self.router)}, r={repr(self.radius)}, {repr(self.children)}>"

    def set_children(self, children: Sequence[Node]) -> None:
        """
        Set the children of this parent node.

        :param children: A sequence of child nodes to be set as children of this parent node.
        """
        self.router = children[0].router
        self.children.clear()
        for child in children:
            self._add_child(child)
        self.radius = max(self.distance(child) for child in children)

    def add_child(self, child: Node) -> None:
        """
        Add a child node to this parent node.

        :param child: The child node to be added.
        """
        if len(self.children) >= self.capacity:
            self.split(child)
        else:
            self._add_child(child)

    def _add_child(self, child: Node) -> None:
        child.parent = self
        self.children.append(child)
        self.radius = max(self.radius, self.distance(child))

    def insert(self, value: Value) -> None:
        """
        Insert a value into the subtree rooted at this parent node.

        :param value: The value to be inserted.
        """
        if isinstance(self.children[0], ValueNode):
            self.add_child(ValueNode(self.tree, value))
        else:
            self.children: list[ParentNode]
            self.radius = max(self.radius, self.distance(value))
            node = min(self.children, key=lambda x: x.distance(value))
            node.insert(value)

    def covers(self, value: Value) -> bool:
        """
        Check if this parent node covers the given value.

        :param value: The value to check.
        :return: True if the parent node covers the value, False otherwise.
        """
        return self.distance(value) <= self.radius

    def increase_required(self, value: Value) -> Distance:
        """
        Calculate the increase in the radius required to cover the given value.

        :param value: The value to calculate the increase for.
        :return: The increase in the radius required to cover the value.
        """
        return self.distance(value) - self.radius

    def __len__(self) -> int:
        return len(self.children)

    def split(self, node: Node) -> None:
        """
        Split this parent node when it reaches its capacity.

        :param node: The node that caused the split.
        """
        a_list, b_list = self.promote_and_partition(node)
        self.set_children(a_list)
        new_node = self.__class__(tree=self.tree, children=b_list)
        if self.parent is None:
            self.parent = ParentNode(tree=self.tree, children=[self, new_node])
        else:
            self.parent.add_child(new_node)

    def promote_and_partition(self, node: Node) -> tuple[list, list]:
        """
        Promote two nodes to be the new routers and partition the children.

        :param node: The node that caused the split.
        :return: A tuple containing two lists of nodes, one for each promoted router.
        """
        a, b, *candidates = chain(self.children, [node])
        a_list, b_list = [a], [b]
        for item in candidates:
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
