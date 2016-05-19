from pywrap.defaultconfig import Config
from pywrap.testing import full_paths


config = Config()
config.ignore_class(full_paths("ignoreclass.hpp")[0], class_name="MyClassA")
config.ignore_method(class_name="MyClassB", method_name="myMethod")