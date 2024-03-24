import click


from omg.odoo import Odoo
from omg.core.settings import get_settings


settings = get_settings()  # pylint: disable=C0413


@click.command()
@click.argument("path")
def skeleton(path):
    """Generate level-1 base code from source."""

    odoo = Odoo.load_path(path)
    # print(odoo.modules)

    for name, module in odoo.modules.items():
        module.write()
