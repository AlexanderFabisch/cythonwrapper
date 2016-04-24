from pywrap.templates import render
from nose.tools import assert_raises


def test_render_fails():
    assert_raises(IOError, render, "no_template_with_this_name")
