pywrap
======

Installation
------------

Install the package with::

    python setup.py install

Usage
-----

We can generate a Python extension that wraps a library deined in a C++ header
with::

    pywrap <header> <target>

The result is located in the directory <target> and can be build with::

    python setup.py build_ext -i

Documentation
-------------

The docmentation of this project can be found in the directory `doc`. To
build the documentation, run e.g. (on unix)::

    cd doc
    make html

Tests
-----

You can use nosetests to run the tests of this project in the root directory::

    nosetests

Version Control
---------------

Git is used for version control.
