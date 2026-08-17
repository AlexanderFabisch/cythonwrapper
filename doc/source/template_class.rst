==============
Template Class
==============

There is no syntax support for templates in Python because it is a language
with dynamic types. That means we cannot directly wrap template types in
Python. We have to specify how the template types should be set. In order to
do that we can create a custom configuration, e.g.

.. code:: python

    from pywrap.defaultconfig import Config
    config = Config()
    config.register_class_specialization("A", "Ad", {"T": "double"})

The corresponding C++ header looks like this:

.. literalinclude:: ../../test/templateclass.hpp
   :language: c++
   :linenos:

The result will be a Python class Ad that has a constructor that takes a double,
a method get that returns a double and a field a that is a double.
