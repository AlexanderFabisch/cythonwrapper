cythonwrapper
=============

Automatically generate a Cython wrapper for C++ code.

Example
-------

Suppose you have a C++ header myheader.hpp.

.. code-block:: c++

    class A
    {
    public:
        double plus2(double d)
        {
            return d + 2.0;
        }
    };

... and you would be able to use it in Python just like

.. code-block:: python

    from myheader import A
    a = A()
    b = 3.213
    c = a.plus2(b)

This is a tool that can do this for you! It will automatically parse the C++
header and generate a wrapper based on Cython for the C++ header. It will
even manage all the type conversions between C++ and Python for you.

Usage
-----

We can generate a Python extension that wraps a library defined in C++ header
with:

.. code-block:: bash

   pywrap <headers> --sources <sources> --modulename <name> --outdir <directory>

The result is located in the directory and can be build with:

.. code-block:: bash

    python setup.py build_ext -i

If this is a header only library we can now simply do the following in
Python:

.. code-block:: python

    from <name> import *

If we must link against a library or we have to compile C++ source files,
we will have to add that to the setup.py that has been generated.
Note that you can use this as a Pyhon library that you can use in your
setup.py as well.

Contents
--------

.. toctree::
   :maxdepth: 1

   function
   template_class
   complex_example
   architecture
   memory_management

:ref:`search`
