# Release History

## Version 0.2

Not released yet.

### Bugfixes

* libclang 3.7 and 3.8 are now supported.

### Features

* Diagnostics from clang are now printed as warning or raised as exceptions.
* The first function or method of multiple overloaded versions is exposed by
  the Python wrapper because Cython cannot handle overloading.
* Methods from base classes are copied to subclasses.
* Avoid name clashes with getter and setter of fields.

## Version 0.1

2017/04/03

First public release.
