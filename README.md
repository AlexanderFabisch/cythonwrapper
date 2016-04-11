# cythonwrapper

Automatically generates a Cython wrapper for C++ code (prototype)

## Example

Suppose you have a C++ header `myheader.hpp`

```cpp
class A
{
public:
    double plus2(double d)
    {
        return d + 2.0;
    }
};
```

... and you would be able to use it in Python just like

```python
from myheader import CppA
a = CppA()
b = 3.213
c = a.plus2(b)
```

This is a tool that can do this for you! It will automatically parse the
C++ header and generate a wrapper based on Cython for the C++ header. It
will even manage all the type conversions between C++ and Python for you.

( At least that is the goal. ;) )

## Install

Install the package with:

    python setup.py install

## Usage

We can generate a Python extension that wraps a library defined in C++ header
with:

    pywrap <headers> --modulename <name> --outdir <directory>

The result is located in the directory <target> and can be build with:

    python setup.py build_ext -i

If this is a header only library we can now simply do the following in
Python:

```python
from <name> import *
```

If we must link against a library or we have to compile C++ source files, we
will have to add that to the `setup.py` that has been generated.

## Documentation

The docmentation of this project can be found in the directory `doc`. To
build the documentation, run e.g. (on unix):

    cd doc
    make html

## Development

### Git

You can get the latest sources with:

    git clone https://github.com/AlexanderFabisch/cythonwrapper.git

### Testing

You can use nosetests to run the tests of this project in the root directory::

    nosetests
