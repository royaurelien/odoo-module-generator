from typing import List

from pydantic import BaseModel

from omg.core.settings import get_settings

settings = get_settings()


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


class IrModelAccess(BaseModel):
    __fields__ = [
        "id",
        "name",
        "model_id",
        "group_id",
        "perm_read",
        "perm_write",
        "perm_create",
        "perm_unlink",
    ]

    path: str = ""
    lines: List[IrModelAccessLine] = []


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
