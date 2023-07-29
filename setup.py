from setuptools import find_packages, setup

setup(
    name="omg",
    version="0.1.0",
    description="Odoo Module Generator",
    url="https://github.com/royaurelien/odoo-module-generator",
    author="Aurelien ROY",
    author_email="roy.aurelien@gmail.com",
    license="BSD 2-clause",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "odoo_analyse",
        "black",
        "jinja2",
    ],
    # extras_require={"graph": ["graphviz", "psycopg2"]},
    entry_points={
        "console_scripts": [
            "omg = omg.main:cli",
        ],
    },
)
