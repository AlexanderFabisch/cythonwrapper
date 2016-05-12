import warnings
from .ast import TemplateClazzSpecialization, Function, Param, Method


class Specializer(object):
    def __init__(self, config):
        self.config = config

    def specialize(self, general):
        try:
            specs = self._lookup_specification(general)
        except LookupError as e:
            warnings.warn(e.message)
            general.ignored = True
            return []

        return self._specialize(general, specs)

    def _lookup_specification(self, general):
        key = self._key(general)
        if key not in self.config.registered_template_specializations:
            raise LookupError(
                "No template specialization registered for template method "
                "'%s' with the following template types: %s"
                % (key, ", ".join(general.template_types)))
        return self.config.registered_template_specializations[key]

    def _key(self, general):
        if general.namespace != "":
            return "%s::%s" % (general.namespace, general.name)
        else:
            return general.name

    def _replace_specification(self, tipe, spec):
        return spec.get(tipe, tipe)

    def _specialize(self, general, specs):
        raise NotImplementedError()


class ClassSpecializer(Specializer):
    def __init__(self, config):
        super(ClassSpecializer, self).__init__(config)

    def _specialize(self, general, specs):
        specialized_classes = []

        for name, spec in specs:
            types = [spec[t] for t in general.template_types]
            cppname = "%s[%s]" % (general.name, ", ".join(types))
            specialized = TemplateClazzSpecialization(
                general.filename, general.namespace, name, cppname, spec)
            specialized_classes.append(specialized)

        return specialized_classes


class FunctionSpecializer(Specializer):
    """Convert a template method to a method."""
    def __init__(self, config):
        super(FunctionSpecializer, self).__init__(config)

    def _specialize(self, general, specs):
        specialized_functions = []
        for name, spec in specs:
            result_type = self._replace_specification(general.result_type, spec)

            specialized = Function(general.filename, general.namespace, name,
                                   result_type)

            for arg in general.arguments:
                tipe = self._replace_specification(arg.tipe, spec)
                specialized.arguments.append(Param(arg.name, tipe))

            specialized_functions.append(specialized)
        return specialized_functions


class MethodSpecializer(Specializer):
    """Convert a template method to a method."""
    def __init__(self, config):
        super(MethodSpecializer, self).__init__(config)

    def _key(self, general):
        return "%s::%s" % (general.class_name, general.name)

    def _specialize(self, general, specs):
        specialized_methods = []
        for name, spec in specs:
            result_type = self._replace_specification(general.result_type, spec)

            specialized = Method(name, result_type, general.class_name)

            for arg in general.arguments:
                tipe = self._replace_specification(arg.tipe, spec)
                specialized.arguments.append(Param(arg.name, tipe))

            specialized_methods.append(specialized)
        return specialized_methods