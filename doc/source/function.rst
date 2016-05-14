========
Function
========

Converting functions with primitive data types is not a problem at all. For
example, take the following C++ functions.

.. literalinclude:: ../../test/function.hpp
   :language: c++
   :linenos:

`pywrap` will automatically generate a wrapper that can be used as follows:

.. code-block:: python

   from function import fun1, fun2
   print(fun1(1))
   print(fun2())