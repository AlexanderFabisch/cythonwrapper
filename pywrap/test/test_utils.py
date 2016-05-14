from pywrap.utils import lines, indent_block, from_camel_case, make_header
from pywrap.testing import assert_equal_linewise
from nose.tools import assert_equal


def test_indent_block():
    block = lines("a", "", "b")
    indented_block = indent_block(block, 1)
    assert_equal_linewise(indented_block, lines("    a", "", "    b"))


def test_from_camel_case():
    assert_equal(from_camel_case("MyFunctionName"), "my_function_name")
    assert_equal(from_camel_case("myFunctionName"), "my_function_name")


def test_make_header():
    assert_equal_linewise(
        make_header("a b c d"),
        lines(
            "+" + "=" * 78 + "+",
            "| a b c d" + " " * 70 + "|",
            "+" + "=" * 78 + "+"
        )
    )