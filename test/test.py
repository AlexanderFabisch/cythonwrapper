import pywrap.cython as pycy
import os
from sklearn.utils.testing import assert_warns_message


PREFIX = os.sep.join(__file__.split(os.sep)[:-1])


def full_path(filename):
    if PREFIX == "":
        return filename
    else:
        return PREFIX + os.sep + filename


def test_twoctors():
    assert_warns_message(UserWarning, "'A' has more than one constructor",
                         pycy.make_cython_wrapper, full_path("twoctors.hpp"))
