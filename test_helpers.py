import random

from hypothesis import given, strategies as st, assume

from mtree4 import PriorityQueue, LimitedSet


@given(...)
def test_pq(value_to_priority: dict[float, int], pops: list[bool]):
    contained = set()
    pq = PriorityQueue()
    for v, p in value_to_priority.items():
        contained.add((p, v))
        pq.push(p, v)
        if pops and pops.pop():
            p, v = pq.pop()
            assert p == min(contained)[0]
            contained.remove((p, v))
    while contained:
        p, v = pq.pop()
        assert p == min(contained)[0]
        contained.remove((p, v))


@given(value_to_priority=..., k=st.integers(min_value=1), pops=...)
def test_limited_set(value_to_priority: dict[int, int], k: int, pops: list[bool]):
    limited_set = LimitedSet(k)
    for item, p in value_to_priority.items():
        before = limited_set.items.copy()
        limited_set.add(p, item)
        assert limited_set.items >= before
        if pops and pops.pop():
            removal = random.choice(list(limited_set.items))
            limited_set.discard(removal)
            assert removal not in limited_set.items
