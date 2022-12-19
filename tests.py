import random
from heapq import nsmallest
from string import ascii_letters, ascii_lowercase
from time import time

from mtree3 import MTree, _default_distance, slow, counter, _f, RouterNode


def random_string(n=100):
    return ''.join(random.choices(ascii_lowercase, k=n))


def test_something():
    random.seed(42)
    size = 10 ** 4
    # numbers = [random.random() * size for _ in range(size)]
    # numbers = random.sample(range(0, size*10, 2), size)
    print()
    strings = list({random_string() for _ in range(size)})
    random.shuffle(strings)
    for cap in [8]:
        _f.cache_clear()
        start = time()
        m = MTree(strings, capacity=cap)
        print('tree', time() - start)
        k = 3
        for _ in range(1):
            needle = random_string()


            counter[0] = 0
            start = time()
            a = sorted(m.knn(needle, k))
            print(counter, time() - start)

            _f.cache_clear()
            counter[0] = 0
            start = time()
            b = sorted(nsmallest(k, strings, key=lambda x: _default_distance(x, needle)))
            # b = min(numbers, key=lambda x: _default_distance(x, needle))
            print(counter, time() - start)


            for x in a:
                d1 = _default_distance(x, needle)
                d2 = _default_distance(b[-1], needle)
                assert d1 <= d2
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

def test_a():
    size = 10 ** 4
    # numbers = [random.random() * size for _ in range(size)]
    # numbers = random.sample(range(0, size*10, 2), size)
    print()
    strings = list({random_string(100) for _ in range(size)})
    random.shuffle(strings)
    m = MTree(strings, capacity=4)

    stack = [(m.root,)]
    while stack:
        path = stack.pop()
        node = path[-1]
        for child in node.children:
            assert child.parent == node
            if isinstance(child, RouterNode):
                stack.append(path + (child,))
            else:
                for parent in path:
                    assert parent.distance(child.router) <= parent.radius
test_a()