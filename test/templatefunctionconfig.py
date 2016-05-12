from pywrap.defaultconfig import Config


config = Config()
config.register_function_specialization("addOne", "add_one_i", {"T": "int"})
config.register_function_specialization("addOne", "add_one_d", {"T": "double"})
