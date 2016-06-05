from nose.tools import assert_false
from pywrap.testing import cython_extension_from
from nose.tools import assert_equal


def test_fails():
    with cython_extension_from("fails.hpp", assert_warn=UserWarning,
                               warn_msg="Ignoring method"):
        from fails import A
        assert_false(hasattr(A, "my_function"))


def test_twoctors():
    with cython_extension_from("twoctors.hpp", assert_warn=UserWarning,
                               warn_msg="'A' has more than one constructor"):
        pass


def test_no_default_constructor():
    with cython_extension_from("nodefaultctor.hpp"):
        from nodefaultctor import A
        a = A()
        a.set_member(5)


def test_python_keyword_conversion():
    with cython_extension_from("pythonkeywords.hpp"):
        from pythonkeywords import my_fun
        assert_equal(my_fun(1, 2, 3), 6)
