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


class IrModelAccessLine(BaseModel):
    id: str
    name: str
    model_id: str
    group_id: str
    perm_read: bool = True
    perm_write: bool = True
    perm_create: bool = True
    perm_unlink: bool = True


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

    def add_line(
        self,
        model,
        group,
        perm_read=True,
        perm_write=True,
        perm_create=True,
        perm_unlink=True,
    ):
        slugified_model = model.replace(".", "_")
        name = f"access_{slugified_model}"
        vals = {
            "id": name,
            "name": name,
            "model_id": f"model_{slugified_model}",
            "group_id": group,
            "perm_read": perm_read,
            "perm_write": perm_write,
            "perm_create": perm_create,
            "perm_unlink": perm_unlink,
        }
        line = IrModelAccessLine(**vals)
        self.lines.append(line)

    def add_lines(self, lines):
        for line in lines:
            self.add_line(**line)


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
