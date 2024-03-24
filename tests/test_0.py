from omg.odoo import Odoo


def test_1():
    path = "./source/module_a"
    odoo = Odoo.load_path(path)

    print(odoo.modules)
