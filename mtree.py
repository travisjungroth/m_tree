# from __future__ import annotations
#
# from abc import ABC, abstractmethod
# from dataclasses import dataclass
# from numbers import Number
# from operator import itemgetter
# from typing import Any, Optional, Union, Type, Callable
#
# Value = Type['Value']
# Distance = Type['Distance']
#
#
# @dataclass()
# class MTree:
#     distance: Callable[[Value, Value], Distance]
#     root: Node
#
#
# class Node(ABC):
#     tree: MTree
#     entries: list[Entry]
#     parent_entry: Union[InternalEntry, LeafEntry, None]
#     parent_node: Node
#
#     def distance_to_parent(self, value: Value) -> Optional[Distance]:
#         if self.parent_entry is None:
#             return None
#         return self.tree.distance(value, self.parent_entry.value)
#
#     @abstractmethod
#     def insert(self, value: Value) -> None:
#         pass
#
#     def is_root(self) -> bool:
#         return self.tree.root is self
#
#     def split(self, value: Value):
#         if not self.is_root():
#             parent_entry = self.parent_entry
#             parent_node = self.parent_node
#         # promote
#         route1, route2 = value, self.entries[-1].value
#         # partition
#         new_node = self.__class__()
#
#         pass
#
# @dataclass()
# class InternalNode(Node):
#     tree: MTree
#     entries: list[InternalEntry]
#     parent_entry: Optional[InternalEntry]
#     parent_node: Node
#     capacity: int = 100
#
#     def insert(self, value: Value):
#         distances: list[tuple[Entry, Distance]] = [
#             (entry, self.tree.distance(value, entry.value))
#             for entry in self.entries
#         ]
#         entry, distance = min(distances, key=itemgetter(1))
#         if distance >= entry.covering_radius:
#             entry, distance = min(distances, key=self._radius_increase)
#             entry.covering_radius = distance
#         return entry.covering_tree.insert
#
#     @staticmethod
#     def _radius_increase(item: tuple[Entry, Distance]) -> Distance:
#         return item[1] - item[0].covering_radius
#
#
# @dataclass()
# class LeafNode(Node):
#     tree: MTree
#     entries: list[LeafEntry]
#     parent_entry: Optional[InternalEntry]
#     parent_node: Node
#     capacity: int = 100
#
#     def insert(self, value: Value):
#         if len(self.entries) < self.capacity:
#             self.store(value)
#         else:
#             self.split(value)
#
#     def store(self, value: Value):
#         distance = self.distance_to_parent(value)
#         entry = LeafEntry(value, distance)
#         self.entries.append(entry)
#
#
# @dataclass()
# class InternalEntry:
#     """
#     Property 1 The covering radius of a routing object, Or, satisfies the inequality
# d(Oj , Or) ≤ r(Or), for each object Oj stored in the covering tree of Or.
#     """
#     value: Value  # routing object
#     covering_radius: Distance  # > 0
#     covering_tree: Node
#     distance_to_parent: Optional[Distance]
#
#
# @dataclass()
# class LeafEntry:
#     value: Value  # object
#     distance_to_parent: Optional[Distance]
#
#
# Entry = Union[InternalEntry, LeafEntry]
