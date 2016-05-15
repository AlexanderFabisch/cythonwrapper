from pywrap.testing import cython_extension_from
import os
import numpy as np
from numpy.testing import assert_array_equal
from nose.plugins.skip import SkipTest


def test_convert_vector():
    eigen3_incdir = "/usr/include/eigen3"
    if not os.path.exists(eigen3_incdir):
        raise SkipTest("Eigen 3 include directory '%s' not found"
                       % eigen3_incdir)

    with cython_extension_from("eigen.hpp", custom_config="eigenconfig.py",
                               incdirs=eigen3_incdir):
        from eigen import make
        a = np.ones(5)
        assert_array_equal(make(a), a * 2.0)