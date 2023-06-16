from itertools import repeat

from hypothesis import strategies as st, given

from m_tree import default_distance


def elements(n):
    def g(f):
        strats = [st.integers(), st.text()]
        return given(st.one_of(*[st.tuples(*repeat(s, n)) for s in strats]))(f)
    return g


@elements(3)
def test_triangle(items):
    a, b, x = items
    assert default_distance(a, b) <= default_distance(a, x) + default_distance(x, b)


@elements(2)
def test_commutative(items):
    a, b = items
    assert default_distance(a, b) == default_distance(b, a)


@elements(2)
def test_positivity(items):
    a, b = items
    dist = default_distance(a, b)
    if a == b:
        assert dist == 0
    else:
        assert dist > 0
