import random
from time import time

from mtree3 import MTree, _default_distance


def test_something():
    random.seed(42)
    size = 10 ** 4
    numbers = random.sample(range(size*10), size)
    # print(numbers)
    # for m in [MTree(numbers, capacity=4), set(numbers)]:
    #     start = time()
    #     assert -1 not in m
    #     for n in numbers:
    #         assert (n in m)
        #
        # print(time() - start)
    start = time()
    m = MTree(numbers, capacity=8)
    print(time() - start)
    start = time()
    needle = size // 4
    a = m.closest(needle)
    print(time() - start)
    start = time()
    b = min(numbers, key=lambda x: _default_distance(x, needle))
    print(time() - start)
    assert a == b
    # start = time()
    # size // 2 in m
    # print(time() - start)
    # m = MTree([], capacity=2)
    # seen = []
    # for i, n in enumerate(numbers):
    #     seen.append(n)
    #     m.insert(n)
    #     for s in seen:
    #         assert s in m, i
