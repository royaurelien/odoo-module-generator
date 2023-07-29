# MyApp CLI

This page provides documentation for our command line tools.

----------

## Installation

Install from PyPI:
```bash
pip install myapp
```

## Quickstart

*On first launch, you will be asked to enter certain parameters.*

Create project :

`project name` is the name of the online database you want to create locally.
```bash
myapp project new <project name>
```

Run project :
```bash
myapp project run <project name> --reload
```

Update modules :
```bash
myapp project update-modules <project name> <database name> module1,module2
```
