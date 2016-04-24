from pywrap.ast import Includes
from nose.tools import assert_true


def test_include_string():
    inc = Includes()
    inc.add_include_for("string")
    assert_true(inc.stl["string"])


def test_include_map():
    inc = Includes()
    inc.add_include_for("map[string, int]")
    assert_true(inc.stl["map"])
    assert_true(inc.stl["string"])