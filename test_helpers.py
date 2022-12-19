from hypothesis import given, strategies as st, assume

from mtree4 import PriorityQueue, FixedPQ


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
def test_fixed_pq(value_to_priority: dict[int, int], k: int, pops: list[bool]):
    seen = set()
    pq = FixedPQ(k)
    for item, p in value_to_priority.items():
        pq.push(p, item)
        seen.add(item)
        if pops and pops.pop():
            pq.discard(seen.pop())
    last_p = float('inf')
    while pq:
        item = pq.pop()
        p = value_to_priority[item]
        assert p <= last_p
        last_p = p