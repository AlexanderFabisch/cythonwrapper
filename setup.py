#!/usr/bin/env python


from distutils.core import setup
import os
import pywrap


if __name__ == "__main__":
    setup(name='pywrap',
          version=pywrap.__version__,
          author='Alexander Fabisch',
          author_email='afabisch@googlemail.com',
          url='TODO',
          description='Generator for Python and C++ wrappers',
          long_description=open('README.rst').read(),
          license='New BSD',
          scripts=["bin" + os.sep + "pywrap"],
          packages=['pywrap'],)
