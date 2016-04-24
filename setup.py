#!/usr/bin/env python
from distutils.core import setup
import os
import pywrap


def check_dependencies():
    try:
        from Cython.Build import cythonize
    except ImportError:
        print("ERROR: install Cython")
    try:
        import clang.cindex
    except:
        print("ERROR: Install 'python-clang-3.5' and 'libclang-3.5-dev'. "
              "Note that a recent operating system is required, e.g. "
              "Ubuntu 14.04.")


if __name__ == "__main__":
    check_dependencies()
    setup(name='pywrap',
          version=pywrap.__version__,
          author=pywrap.__author__,
          author_email=pywrap.__author_email__,
          url=pywrap.__url__,
          description=pywrap.__description__,
          long_description=open("README.md").read(),
          license="New BSD",
          scripts=["bin" + os.sep + "pywrap"],
          packages=['pywrap'],
          package_data={'pywrap': ['template_data/*.template']},
          requires=['numpy', 'cython', 'Jinja2'])
