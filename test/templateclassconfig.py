from pywrap.defaultconfig import Config


config = Config()
specs = {
    "A": [
        ("Ai", {"T": "int"})
    ]
}
config.registered_template_specializations.update(specs)