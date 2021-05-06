import pickle
import sys
import io


def dump_load(val):
    t = pickle.dumps(val)
    assert isinstance(t, bytes) # assert will raise an AssertionError if false
    t = pickle.loads(t)
    assert t == val


dump_load(1)
dump_load(1.0)
dump_load("str")
dump_load(b"bytes")
dump_load((1,))
dump_load([1, 2])
dump_load({1:2, 3: 4})

try:
    pickle.loads(b"1; import micropython")
    assert 0, "SyntaxError expected"
except SyntaxError:
    pass