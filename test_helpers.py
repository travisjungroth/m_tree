from hypothesis import given

from mtree4 import PriorityQueue


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
