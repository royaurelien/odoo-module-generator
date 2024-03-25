import ast

import astor

from omg.common.node import GetFields

# from omg.common.tools import generate, get_arg, get_assign, get_keyword
# from omg.core.models import File


MANIFESTS = ["__manifest__.py", "__odoo__.py", "__openerp__.py"]
MODEL_TYPES = ["AbstractModel", "TransientModel", "Model"]


class Model:
    def __init__(self, name=None, inherit=None, inherits=None, fields=None, funcs=None):
        self.name = name
        self._obj = None
        self.inherit = set(inherit or [])
        self.inherits = inherits or {}
        self.fields = fields or {}
        self.funcs = funcs or {}

    @property
    def _name(self):
        return list(self.inherit)[0] if self.inherit and not self.name else self.name

    @property
    def is_stored(self) -> bool:
        return self.ttype == "Model"

    @property
    def is_new(self) -> bool:
        return self.name and not self.inherit

    @property
    def has_fields(self) -> bool:
        return bool(self.fields)

    @property
    def filename(self) -> str:
        return self._name.replace(".", "_") + ".py"

    @property
    def classname(self) -> str:
        return "".join(map(str.capitalize, self._name.split(".")))

    @property
    def sql_name(self) -> str:
        return "_".join(self._name.split("."))

    @property
    def ttype(self):
        base = self._obj.bases[0]
        return ".".join([base.value.id, base.attr])

    def __repr__(self) -> str:
        return f"<Model: {self.name}>"

    def _parse_assign(self, obj: ast.Assign, content: str) -> None:
        assignments = [k.id for k in obj.targets if isinstance(k, ast.Name)]
        if len(assignments) != 1:
            return

        assign, value = assignments[0], obj.value
        if assign == "_name":
            if not isinstance(value, ast.Constant):
                return

            self.name = ast.literal_eval(value)
        elif assign == "_inherit":
            if isinstance(value, ast.Name) and value.id == "_name":
                self.inherit.add(self.name)
            elif not isinstance(value, ast.Name):
                value = ast.literal_eval(value)
                if isinstance(value, list):
                    self.inherit.update(value)
                else:
                    self.inherit.add(value)
        elif assign == "_inherits":
            inhs = ast.literal_eval(value)
            if isinstance(inhs, dict):
                self.inherits.update(inhs)
                # self.fields.update({k: Field("fields.Many2one") for k in inhs.values()})

    @classmethod
    def from_ast(cls, obj: ast.ClassDef, content: str) -> "Model":
        model = cls()
        for child in obj.body:
            if isinstance(child, ast.Assign):
                model._parse_assign(child, content)

        # Force classname to CamelCase
        obj.name = model.classname

        model._obj = obj

        return model

    def _get_fields(self):
        fields = GetFields()
        fields.visit(self._obj)

        return fields._fields

    def fields_matrix(self):
        return {k: "" for k in self._get_fields()}

    def export(self):
        return astor.to_source(self._obj)
