#!/usr/bin/env python


from distutils.core import setup
import os
import pywrap


if __name__ == "__main__":
    setup(name='pywrap',
          version=pywrap.__version__,
          author=pywrap.__author__,
          author_email=pywrap.__author_email__,
          url=pywrap.__url__,
          description=pywrap.__description__,
          long_description=open("README.rst").read(),
          license="New BSD",
          scripts=["bin" + os.sep + "pywrap"],
          packages=['pywrap'],)
