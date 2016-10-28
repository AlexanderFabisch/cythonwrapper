from pywrap.testing import cython_extension_from
from pywrap.utils import lines
from nose.tools import assert_multi_line_equal, assert_equal


def test_comments():
    with cython_extension_from("comments.hpp"):
        from comments import MyClass, MyEnum
        assert_multi_line_equal(
            lines("This is a brief class description.",
                  "    ",
                  "    And this is a detailed description.",
                  "    "),
            MyClass.__doc__)
        assert_equal("Brief.", MyClass.method.__doc__.strip())
        assert_equal("Brief description of enum.", MyEnum.__doc__.strip())
