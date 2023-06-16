import random

from hypothesis import given, strategies as st, settings

from m_tree.helpers import PriorityQueue, LimitedSet


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


# rerun this test many times since it is probabilistic
@settings(max_examples=1000)
@given(value_to_priority=..., k=st.integers(min_value=1), pops=...)
def test_limited_set(value_to_priority: dict[int, int], k: int, pops: list[bool]):
    limited_set = LimitedSet(k)
    for item, p in value_to_priority.items():
        before = limited_set.items.copy()
        limited_set.add(p, item)
        assert len(limited_set.items) <= k
        if len(before) < k:
            assert item in limited_set.items
            assert limited_set.items == before | {item}
        else:
            dropped = (before | {item}) - limited_set.items
            assert item in limited_set.items or item in dropped
            if dropped:
                dropped_item, = dropped
                drop_pri = value_to_priority[dropped_item]
                assert all(drop_pri >= value_to_priority[i] for i in limited_set.items)

        if pops and pops.pop():
            removal = random.choice(list(limited_set.items))
            limited_set.discard(removal)
            assert removal not in limited_set.items
