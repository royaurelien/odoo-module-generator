from typing import List

from pydantic import BaseModel, computed_field

# from pydantic.functional_serializers import PlainSerializer


BaseModel.model_config["protected_namespaces"] = ()


class RepositoryTemplate(BaseModel):
    name: str = "royaurelien/odoo-repository-template"
    branch: str = "master"
    commit_enable: bool = True
    commit_message: str = "[NEW] Quality / Pre-commit"
    post_hook: list = [
        "pre-commit install",
        # "pre-commit run --all-files",
    ]


class DefaultManifest(BaseModel):
    odoo_version: str = "16.0"
    module_version: str = "1.0.0"
    # version: str = "16.0.1.0.0"
    category: str
    website: str
    author: str
    mainteners: List[str]
    license: str


class Manifest(DefaultManifest):
    name: str = "Module name"
    description: str = "Publish your customer references"
    summary: str = "Publish your customer references"
    external_dependencies: dict = {}
    data: List[str] = []
    demo: List[str] = []
    assets: dict = {}
    depends: List[str] = [
        "base",
    ]
    installable: bool = True
    auto_install: bool = False
    application: bool = False

    @computed_field(return_type=str)
    @property
    def version(self):
        return f"{self.odoo_version}.{self.module_version}"

    def add_items(self, key, value):
        """Add items to list fields."""

        attr = getattr(self, key)
        attr += value


class IrModelAccessLine(BaseModel):
    id: str
    name: str
    model_id: str
    group_id: str
    perm_read: int = 1
    perm_write: int = 1
    perm_create: int = 1
    perm_unlink: int = 1

    def to_csv(self):
        data = self.dict()
        data["model_id:id"] = data.pop("model_id")
        data["group_id:id"] = data.pop("group_id")

        return data


class IrModelAccess(BaseModel):
    path: str = ""
    lines: List[IrModelAccessLine] = []

    @staticmethod
    def header():
        keys = list(IrModelAccessLine.schema()["properties"].keys())
        keys[2] = "model_id:id"
        keys[3] = "group_id:id"

        return keys


class Field(BaseModel):
    """
    <field name="name">Custom Sequence</field>
    <field name="company_id" eval="False"/>
    """

    name: str
    value: str = ""
    eval: str = ""
    ref: str = ""
    type: str = ""


class Record(BaseModel):
    """
    <record id="seq_custom_model" model="ir.sequence">
        <field name="name">Custom Sequence</field>
        <field name="code">custom.model</field>
        <field name="prefix">CS</field>
        <field name="padding">5</field>
        <field name="company_id" eval="False"/>
    </record>
    """

    id: str
    model: str
    # fields: list(Field) = []
