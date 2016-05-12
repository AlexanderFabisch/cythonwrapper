from pywrap.defaultconfig import Config


config = Config()
config.register_class_specialization("A", "Ai", {"T": "int"})
