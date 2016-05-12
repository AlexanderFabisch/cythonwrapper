from pywrap.defaultconfig import Config


config = Config()
specs = {
    "A::addOne": [
        ("add_one_i", {"T": "int"}),
        ("add_one_d", {"T": "double"})
    ]
}
config.register_method_specialization("A", "addOne", "add_one_i", {"T": "int"})
config.register_method_specialization("A", "addOne", "add_one_d",
                                      {"T": "double"})
