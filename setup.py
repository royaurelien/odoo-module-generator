from setuptools import find_packages, setup

setup(
    name="odoo-module-generator",
    version="0.2.0",
    description="Odoo Module Generator",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/royaurelien/odoo-module-generator",
    author="Aurelien ROY",
    author_email="roy.aurelien@gmail.com",
    license="BSD 2-clause",
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
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
    python_requires=">=3.8",
    extras_require={},
    entry_points={
        "console_scripts": [
            "omg = omg.cli:cli",
        ],
    },
)
