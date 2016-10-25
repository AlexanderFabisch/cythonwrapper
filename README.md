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

* default values
* linking to other libraries (you can modify the `setup.py` though)
* integrating other Cython extensions (you can modify the `setup.py` though)

Feel free to work on any of these features. :)

## Why?

I think Cython is a great tool to wrap C++ code in Python. However, it requires a lot of manual work to wrap C++ code: you have to write a file that lists all the classes and functions that you want to use and you must convert custom types manually. A lot of this work can be done automatically. A pitfall is the naming of classes and functions. It is hard to have consistent names while you write a wrapper manually. With this tool you do not rely on every developer on the project to follow the same naming scheme because the names of classes and functions in the wrapper are determined automatically from their C++ decleration.

## Install

Install the package with:

    python setup.py install

## Usage

### Command Line Tool

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

### Python Library

Note that you can use this as a Pyhon library that you can use in your
`setup.py` as well. For now, take a look at the code to understand how
you can do that. You can take a look at the
[main function](https://github.com/AlexanderFabisch/cythonwrapper/blob/master/bin/pywrap#L29)
or at the
[test code](https://github.com/AlexanderFabisch/cythonwrapper/blob/master/pywrap/testing.py)
which should give you a good impression of how to use the library.

### Import Hook

A third option to generate a Python wrapper is to use the import hook:

```python
import pywrap.import_hook
import myheader
a = A()
b = 3.213
c = a.plus2(b)
```

The first import statement will add a module finder that searches for a
C++ header file that corresponds to the name of modules in import statements,
e.g., `myheader.hpp`, and compiles them before they are actually imported.

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
