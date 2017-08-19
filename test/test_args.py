from pywrap.testing import cython_extension_from
from nose.tools import assert_false, assert_true, assert_equal
from pywrap.type_conversion import AbstractTypeConverter
from pywrap.defaultconfig import Config


def test_independent_parts():
    with cython_extension_from(["indeppart1.hpp", "indeppart2.hpp"],
                               modulename="combined"):
        from combined import ClassA, ClassB
        a = ClassA()
        assert_false(a.result())
        b = ClassB()
        assert_true(b.result())


def test_dependent_parts():
    with cython_extension_from(["deppart1.hpp", "deppart2.hpp"],
                               modulename="depcombined"):
        from depcombined import A
        a = A()
        b = a.make()
        assert_equal(b.get_value(), 5)


def test_register_custom_type_converter():
    class CustomTypeConverter(AbstractTypeConverter):
        def matches(self):
            raise NotImplementedError()

        def n_cpp_args(self):
            raise NotImplementedError()

        def add_includes(self, includes):
            raise NotImplementedError()

        def python_to_cpp(self):
            raise NotImplementedError()

        def cpp_call_args(self):
            raise NotImplementedError()

        def return_output(self, copy=True):
            raise NotImplementedError()

        def python_type_decl(self):
            raise NotImplementedError()

        def cpp_type_decl(self):
            raise NotImplementedError()

    config = Config()
    config.registered_converters.append(CustomTypeConverter)

    with cython_extension_from("boolinboolout.hpp", assert_warn=UserWarning,
                               warn_msg="Ignoring method", config=config):
        pass


def test_another_include_dir():
    with cython_extension_from("addincludedir.hpp",
                               incdirs=["anotherincludedir"]):
        from addincludedir import length
        assert_equal(length(3.0, -4.0), 7.0)
