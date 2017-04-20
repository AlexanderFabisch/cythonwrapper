import os
import jinja2
from pkg_resources import resource_filename


def render(template, **kwargs):
    """Render a Jinja2 template.

    Parameters
    ----------
    template : str
        Name of the template file (without '.template' suffix). It must be
        located in the directory 'pywrap/template_data'.

    kwargs : dict
        Template arguments.

    Returns
    -------
    text : str
        Rendered template.
    """
    template_file = resource_filename(
        "pywrap", os.path.join("template_data", template + ".template"))
    if not os.path.exists(template_file):
        raise IOError("No template for '%s' found." % template)
    template = jinja2.Template(open(template_file, "r").read())
    return template.render(**kwargs)


# declaration templates
typedef_decl = """cdef extern from "%(filename)s" namespace "%(namespace)s":
    ctypedef %(underlying_type)s %(tipe)s"""
function_decl = """cdef extern from "%(filename)s" namespace "%(namespace)s":
    %(result_type)s %(name)s(%(args)s)"""
template_function_decl = """cdef extern from "%(filename)s" namespace "%(namespace)s":
    %(result_type)s %(name)s[%(types)s](%(args)s)"""
method_decl = "%(result_type)s %(name)s(%(args)s)"
template_method_decl = "%(result_type)s %(name)s[%(types)s](%(args)s)"
constructor_decl = "%(class_name)s(%(args)s)"
arg_decl = "%(tipe)s %(name)s"
field_decl = "%(tipe)s %(name)s"

# member definitions
ctor_default_def = """    def __init__(cpp.%(name)s self):
        self.%(name)s_thisptr = new cpp.%(name)s()"""
fun_call = "cpp.%(name)s(%(call_args)s)"
ctor_call = "self.thisptr = new cpp.%(class_name)s(%(call_args)s)"
method_call = "self.thisptr.%(name)s(%(call_args)s)"
setter_call = "self.thisptr.%(name)s = %(call_args)s"
getter_call = "self.thisptr.%(name)s"
catch_result = "%(cpp_type_decl)s result = %(call)s"
