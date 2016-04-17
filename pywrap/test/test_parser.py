from pywrap.parser import Includes
from nose.tools import assert_true


def test_include_string():
    inc = Includes()
    inc.add_include_for("string")
    assert_true(inc.string)


def test_include_map():
    inc = Includes()
    inc.add_include_for("map[string, int]")
    assert_true(inc.map)
    assert_true(inc.string)