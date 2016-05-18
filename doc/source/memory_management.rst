=================
Memory Management
=================

Call by Value / Reference
-------------------------

Suppose we have the following decleration in a C++ header:

.. code-block:: c++

    void fun(double& d);
    void fun(double* d);

Function calls are interpreted as call by value for basic types, i.e. even
though the C++ function takes a double pointer and modify its content this
won't change the value of a float passed to the C++ function via the Python
wrapper.

.. code-block:: c++

    void fun(MyClass& c);
    void fun(MyClass* c);

For custom classes this is a different story. The wrapper of a custom class
holds a pointer to the C++ class which will be passed by reference to the
C++ function. This behavior is different because we cannot be sure that
either an assignment operator or a copy constructor exists for the custom
C++ class.

Note that when we pass a reference to an object to the C++ function the object
is owned by its Python wrapper object. That means when the Python wrapper
object will be deleted any reference that is kept within another class instance
to the object points to invalid memory. C++ developers are used to this
behavior but Python developers might be a bit surprised when they see their
first segmentation fault.

Return Values
-------------

Returning basic types like doubles, vectors, maps etc. is straightforward.
With custom classes it is again a little bit more complicated. In the following
case, we must assume that MyClass has a default constructor and a copy
constructor or an assignment operator.

.. code-block:: c++

    MyClass fun();

The function wrapper will create a new Python wrapper object for MyClass
and assign the return value to the wrapped object. In the following case,
we assume that fun creates a new object with new and does not own it any
more (even though fun might actually be a method). The pointer will be
deleted by the corresponding Python wrapper of MyClass.

.. code-block:: c++

    MyClass* fun();
