import os
import jinja2
from pkg_resources import resource_filename


def render(template, **kwargs):
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
method_decl = "        %(result_type)s %(name)s(%(args)s)"
constructor_decl = "        %(class_name)s(%(args)s)"
arg_decl = "%(tipe)s %(name)s"
field_decl = "        %(tipe)s %(name)s"

# member definitions
ctor_default_def = """    def __init__(cpp.%(name)s self):
        self.thisptr = new cpp.%(name)s()
"""
fun_call = "cpp.%(name)s(%(args)s)"
ctor_call = "self.thisptr = new cpp.%(class_name)s(%(args)s)"
method_call = "self.thisptr.%(name)s(%(args)s)"
setter_call = "self.thisptr.%(name)s = %(call_arg)s"
getter_call = "self.thisptr.%(name)s"
catch_result = "%(cpp_type_decl)s result = %(call)s"
