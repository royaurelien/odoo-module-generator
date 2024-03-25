

# Odoo Module Generator

_**omg** Command Line Tool_

![PyPI](https://img.shields.io/pypi/v/odoo-module-generator) ![PyPI](https://img.shields.io/pypi/pyversions/odoo-module-generator)

## Installation

Install from PyPI:
```bash
pip  install  odoo-module-generator
```
## Usage

### Scaffold
#### Module
```bash
omg scaffold module <path>
```
#### Repository
```bash
omg scaffold repo <path>
```
### Update Manifest
```bash
omg update manifest <path>
```
### Codebase (upgrade helper)

 - Run on a single module or folder.
 - Models :
   - Loads only the models used (from `__init__.py`) .
   - Classes renamed to CamelCase using the name attribute (`_name`).
   - Models automatically split by file with automatic naming.
 - Fields :
   - Filtering of field attributes (deletion of compute, help, etc).
   - Explicit naming of arguments in field declarations where possible (comodel_name, inverse_name, string).
   - `help` attribute filled in when a compute field is associated with the `store` attribute (for historical purposes).
 - Others :
	 - Deletion of everything that is not a model (default behaviour, `--no-clean` argument).
	 - Generation of an ir.model.access with default rights when creating models (`_name` without `_inherit`).
	 - Manifest updated.
	 - Creation of an on-demand pre-migration script with full mapping of module fields.
	 - Black formatting applied to generated code.
	 - Automatic validation per module.

```bash
omg codebase <path to module or foler> <version>
```



