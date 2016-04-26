from pywrap.type_conversion import AbstractTypeConverter
from pywrap.defaultconfig import Config


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
