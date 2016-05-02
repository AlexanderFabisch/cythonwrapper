[![Build Status](https://travis-ci.org/AlexanderFabisch/cythonwrapper.png?branch=master)](https://travis-ci.org/AlexanderFabisch/cythonwrapper)

# cythonwrapper

Automatically generates a Cython wrapper for C++ code

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
from myheader import A
a = A()
b = 3.213
c = a.plus2(b)
```

This is a tool that can do this for you! It will automatically parse the
C++ header and generate a wrapper based on Cython for the C++ header. It
will even manage all the type conversions between C++ and Python for you.

At least that is the goal. ;)

There are more examples in the subdirectory `examples`.

## Unsupported Features of C++

Many things are not implemented yet, e.g.

* static methods
* arrays, e.g. `float[3]`
* class templates (template methods and functions are supported)
* linking to other libraries (you can modify the `setup.py` though)
* integrating other Cython extensions (you can modify the `setup.py` though)

Feel free to work on any of these features. :)

## Install

Install the package with:

    python setup.py install

## Usage

We can generate a Python extension that wraps a library defined in C++ header
with:

    pywrap <headers> --sources <sources> --modulename <name> --outdir <directory>

The result is located in the directory <target> and can be build with:

    python setup.py build_ext -i

If this is a header only library we can now simply do the following in
Python:

```python
from <name> import *
```

If we must link against a library or we have to compile C++ source files, we
will have to add that to the `setup.py` that has been generated.

Note that you can use this as a Pyhon library that you can use in your
`setup.py` as well. For now, take a look at the code to understand how
you can do that. You can take a look at the
[main function](https://github.com/AlexanderFabisch/cythonwrapper/blob/master/bin/pywrap#L26)
or at the
[test code](https://github.com/AlexanderFabisch/cythonwrapper/blob/master/pywrap/testing.py)
which should give you a good impression of how to use the library.

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

You can use nosetests to run the tests of this project in the root directory:

    nosetests
