# M-Tree

[![License: MIT](https://img.shields.io/github/license/travisjungroth/m_tree?color=blue)](https://github.com/travisjungroth/m_tree/blob/main/LICENSE)

An M-Tree is an efficient access method for similarity search in [metric spaces](https://en.wikipedia.org/wiki/Metric_space). It has better time complexity than other KNN algorithms. In practice, with a fast distance function, much simpler algorithms are faster. Where it does well is when the distance function is order of magnitudes slower than the tree operations, like an API call or a database query. You should essentially view it as a KNN on a metric space that minimizes the number of distance function calls.

This Python implementation is based on the papers ["M-tree: An Efficient Access Method for Similarity Search in Metric Spaces"](https://www.researchgate.net/publication/2373366_M-tree_An_Efficient_Access_Method_for_Similarity_Search_in_Metric_Spaces) by Paolo Ciaccia, Marco Patella, and Pavel Zezula, and  ["Indexing Metric Spaces with M-Tree"](https://www.researchgate.net/publication/220974334_Indexing_Metric_Spaces_with_M-Tree) by Paolo Ciaccia, Marco Patella, Fausto Rabitti, and Pavel Zezula. It has some simplifications, mainly reducing the types of nodes.

## Usage

```python
from m_tree import MTree

# Create an M-Tree with a custom distance function
mtree = MTree(distance_function=lambda x, y: abs(x - y))

# Insert data points
mtree.insert(5)
mtree.insert(10)
mtree.insert(15)

# Check if a point exists in the M-Tree
print(10 in mtree)  # Output: True

# Find the k-nearest neighbors of a given point
knn = mtree.knn(value=8, k=2)
print(knn)  # Output: [5, 10]
```

## Custom Distance Functions

You can use any distance function that satisfies the properties of a [metric space](https://en.wikipedia.org/wiki/Metric_space) (non-negativity, symmetry, and the triangle inequality). The distance function should take two arguments (data points) and return a non-negative scalar value representing the distance between them.

Example of using the [Manhattan distance](https://en.wikipedia.org/wiki/Taxicab_geometry) function:

```python
from m_tree import MTree

def manhattan_distance(point1, point2):
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

points = [(1, 2), (3, 4), (5, 6), (7, 8)]

mtree = MTree(distance_function=manhattan_distance)

for point in points:
    mtree.insert(point)

knn = mtree.knn(value=(4, 5), k=2)
print(knn)  # Output: [(3, 4), (5, 6)]
```
