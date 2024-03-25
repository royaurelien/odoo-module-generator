from omg.odoo.module import Module


class Odoo:
    def __init__(self):
        self.modules = {}

    @classmethod
    def load_path(cls, path, **config):
        odoo = cls()
        odoo.modules = Module.find_modules(path)

        return odoo
