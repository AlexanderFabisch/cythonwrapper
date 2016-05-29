from pywrap.utils import (lines, indent_block, from_camel_case, make_header,
                          file_ending, hidden_stream, remove_files)
from nose.tools import assert_equal, assert_multi_line_equal, raises


def test_indent_block():
    block = lines("a", "", "b")
    indented_block = indent_block(block, 1)
    assert_multi_line_equal(indented_block, lines("    a", "", "    b"))


def test_from_camel_case():
    assert_equal(from_camel_case("MyFunctionName"), "my_function_name")
    assert_equal(from_camel_case("myFunctionName"), "my_function_name")


def test_make_header():
    assert_multi_line_equal(
        make_header("a b c d"),
        lines(
            "+" + "=" * 78 + "+",
            "| a b c d" + " " * 70 + "|",
            "+" + "=" * 78 + "+"
        )
    )


def test_file_ending():
    assert_equal(file_ending("test.py"), "py")
    assert_equal(file_ending("/path.with/more.dots/test.pxd"), "pxd")


@raises(ValueError)
def test_hide_invalid_stream():
    with hidden_stream(3):
        pass


def test_remove_no_files():
    remove_files(["does", "not", "exist"])
