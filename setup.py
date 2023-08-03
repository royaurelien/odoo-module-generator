from setuptools import find_packages, setup

setup(
    name="omg",
    version="0.1.2",
    description="Odoo Module Generator",
    url="https://github.com/royaurelien/omg",
    author="Aurelien ROY",
    author_email="roy.aurelien@gmail.com",
    license="BSD 2-clause",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.1.6",
        "platformdirs>=3.5.1",
        "pydantic>=2.1.1",
        "pydantic_settings>=2.0.2",
        "black>=23.1.0",
        "jinja2>=3.1.1",
        "requests>=2.28.1",
        "gitpython>=3.1.27",
    ],
    extras_require={},
    entry_points={
        "console_scripts": [
            "omg = omg.cli.main:cli",
        ],
    },
)
