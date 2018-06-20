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
* Enums can be defined in classes.
* Linking of external libraries.

### Breaking Changes

* Static methods of a class 'CLS' will now have the prefix 'CLS_', e.g.
  'CLS_static_method()'.
* Fixed typo in interface of Config: renamed all occurences of 'decleration'
  to 'declaration'. In particular, the method Config.add_decleration()
  has been renamed to Config.add_declaration().

## Version 0.1

2017/04/03

First public release.
