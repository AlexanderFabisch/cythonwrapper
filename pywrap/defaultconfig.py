class Config(object):
    def __init__(self):
        # file endings
        self.cpp_header_endings = ["h", "hh", "hpp"]
        self.python_file_ending = "py"
        self.pyx_file_ending = "pyx"
        self.pxd_file_ending = "pxd"

        # Operator mapping
        # overview of Cython operators:
        # http://docs.cython.org/src/reference/special_methods_table.html
        # overview of C++ operators:
        # http://en.cppreference.com/w/cpp/language/operators
        self.operators = {
            "operator()": "__call__",
            "operator[]": "__getitem__",
            "operator+": "__add__",
            "operator-": "__sub__",
            "operator*": "__mul__",
            "operator/": "__div__",
            "operator%": "__mod__",
            "operator&&": "__and__",
            "operator&": "__and__",
            "operator||": "__or__",
            "operator|": "__or__",
            "operator+=": "__iadd__",
            "operator-=": "__isub__",
            "operator*=": "__imul__",
            "operator/=": "__idiv__",
            "operator%=": "__imod__",
            "operator&=": "__iand__",
            "operator|=": "__ior__",
        }
        self.call_operators = {
            "operator()": "call",
            "operator[]": "getitem",
            "operator+": "add",
            "operator-": "sub",
            "operator*": "mul",
            "operator/": "div",
            "operator%": "mod",
            "operator&&": "opand",
            "operator&": "opand",
            "operator||": "opor",
            "operator|": "opor",
            "operator+=": "iadd",
            "operator-=": "isub",
            "operator*=": "imul",
            "operator/=": "idiv",
            "operator%=": "imod",
            "operator&=": "iand",
            "operator|=": "ior",
        }

        self.registered_converters = []
        self.registered_template_specializations = {}
        self.additional_declarations = {}
        self.ignored = []

        self.library_dirs = []
        self.libraries = []

        self.class_to_module = {}

    def cpp_to_py_operator(self, name):
        if name.startswith("operator") and name not in self.operators:
            raise NotImplementedError("Cannot convert C++ operator '%s' to "
                                      "Python operator." % name)
        return self.operators.get(name, name)

    def add_declaration(self, modulename, decl, defined_classes=()):
        """Add declaration manually.

        Parameters
        ----------
        modulename : str
            Name of the module. A declaration file with the name
            '_modulename.pxd' will be created.

        decl : str
            Content of the declaration file.

        defined_classes : iterable, optional (default: ())
            A list of classes that are defined in the declaration and will
            be available in '_modulename'.
        """
        self.additional_declarations[modulename] = decl
        for clazz in defined_classes:
            self.class_to_module[clazz] = modulename

    def register_class_specialization(
            self, cpp_classname, python_classname, template_to_type):
        """Register a specialization for a template class.

        Parameters
        ----------
        cpp_classname : str
            Name of the template class

        python_classname : str
            Name of the specialized template in Python

        template_to_type : dict
            Maps template type names to actual type
        """
        self._register_specialization(cpp_classname, python_classname,
                                      template_to_type)

    def register_function_specialization(
            self, cpp_functionname, python_functionname, template_to_type):
        """Register a specialization for a template function.

        Parameters
        ----------
        cpp_functionname : str
            Name of the template function

        python_functionname : str
            Name of the specialized template in Python

        template_to_type : dict
            Maps template type names to actual type
        """
        self._register_specialization(cpp_functionname, python_functionname,
                                      template_to_type)

    def register_method_specialization(
            self, cpp_classname, cpp_methodname, python_methodname,
            template_to_type):
        """Register a specialization for a template method.

        Parameters
        ----------
        cpp_classname : str
            Name of the class

        cpp_methodname : str
            Name of the template method

        python_methodname : str
            Name of the specialized template in Python

        template_to_type : dict
            Maps template type names to actual type
        """
        self._register_specialization(cpp_classname + "::" + cpp_methodname,
                                      python_methodname, template_to_type)

    def _register_specialization(self, key, name, template_to_type):
        if key not in self.registered_template_specializations:
            self.registered_template_specializations[key] = []
        self.registered_template_specializations[key].append(
            (name, template_to_type))

    def ignore_class(self, filename, class_name):
        """Ignore class during generation of the bindings.

        Parameters
        ----------
        filename : str
            Header file

        class_name : str
            Name of the class that will be ignored
        """
        self.ignore(filename, class_name)

    def is_ignored_class(self, filename, class_name):
        return self.is_ignored(filename, class_name)

    def ignore_method(self, class_name, method_name):
        """Ignore method during generation of the bindings.

        Parameters
        ----------
        class_name : str
            Name of the class

        method_name : str
            Name of the method that will be ignored
        """
        self.ignore(class_name, method_name)

    def is_ignored_method(self, class_name, method_name):
        return self.is_ignored(class_name, method_name)

    def ignore(self, *args):
        self.ignored.append(":".join(args))

    def is_ignored(self, *args):
        return ":".join(args) in self.ignored

    def abstract_class(self, class_name):
        """Prevent class constructor generation by declaring it abstract.

        Parameters
        ----------
        class_name : str
            Name of the abstract class
        """
        self.ignore(class_name, "__init__")

    def is_abstract_class(self, class_name):
        return self.is_ignored(class_name, "__init__")

    def add_library_dir(self, library_dir):
        """Add library directory that is required to build the extension.

        Parameters
        ----------
        library_dir : str
            Directory
        """
        self.library_dirs.append(library_dir)

    def add_library(self, library):
        """Add library that is required to build the extension.

        Parameters
        ----------
        library : str
            Library name
        """
        self.libraries.append(library)
