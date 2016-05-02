from pywrap.defaultconfig import Config


config = Config()
specs = {
    "addOne": [
        ("add_one_i", {"T": "int"}),
        ("add_one_d", {"T": "double"})
    ]
}
config.registered_template_specializations.update(specs)