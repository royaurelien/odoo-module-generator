from typing import List

from pydantic import BaseModel

from omg.core.settings import get_settings

settings = get_settings()

BaseModel.model_config["protected_namespaces"] = ()


class Manifest(BaseModel):
    __prompt__ = [
        "name",
        "description",
        "category",
        "website",
        "author",
        "license",
    ]

    technical_name: str

    name: str = "Module name"
    version: str = "16.0.1.0.0"
    category: str = settings.default_category
    description: str = "Publish your customer references"
    summary: str = "Publish your customer references"
    website: str = settings.default_website
    author: str = settings.default_author
    mainteners: List[str] = settings.default_mainteners
    depends: List[str] = [
        "base",
    ]
    external_dependencies: dict = {}
    data: List[str] = []
    demo: List[str] = []
    assets: dict = {}
    installable: str = True
    auto_install: str = False
    application: str = False
    license: str = settings.default_license

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
