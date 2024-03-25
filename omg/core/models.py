# from pydantic.functional_serializers import PlainSerializer
from collections import OrderedDict, namedtuple
from typing import List

from pydantic import BaseModel, Field, ValidationError, computed_field
from pydantic.type_adapter import TypeAdapter

from omg.common.logger import _logger

File = namedtuple(
    "File",
    ["name", "path", "content"],
)

BaseModel.model_config["protected_namespaces"] = ()


class Question(BaseModel):
    question: str = Field(title="Question")
    default: bool = True

    def prompt(self):
        raise NotImplementedError()


class YesNoQuestion(Question):
    def prompt(self):
        response = self.default
        default = "[Y/n]" if self.default else "[y/N]"

        while True:
            res = input(f"{self.question} {default}: ")
            if not res:
                break

            try:
                response = TypeAdapter(bool).validate_python(res)
            except ValidationError:
                continue
            break
        return response


def convert_string_list_to_list(value):
    if isinstance(value, list):
        return value

    value = value.strip("[]").replace('"', "").replace("'", "")

    if ", " in value:
        value = value.split(", ")
    else:
        value = value.split(",")

    return value


class DefaultQuestion(Question):
    default: str

    def _cast(self, value):
        return value

    def _adaptater(self):
        return TypeAdapter(str)

    def prompt(self):
        response = self.default
        value = self.default

        if isinstance(self.default, list):
            value = ", ".join(self.default) if self.default else "[]"

        while True:
            res = input(f'{self.question} "{value}" ? [Y/n] : ')

            if not res:
                break

            try:
                res = self._cast(res)

                response = self._adaptater().validate_python(res)
            except ValidationError as error:
                _logger.error(error)
                continue
            break
        return response


class DefaultListQuestion(DefaultQuestion):
    default: List[str]

    def _adaptater(self):
        return TypeAdapter(List[str])

    def _cast(self, value):
        return convert_string_list_to_list(value)


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
    __keys__ = [
        "name",
        "description",
        "summary",
        "version",
        "category",
        "author",
        "mainteners",
        "website",
        "depends",
        "external_dependencies",
        "data",
        "demo",
        "assets",
        "installable",
        "auto_install",
        "application",
        "license",
    ]
    __authorized_keys__ = [
        "name",
        "data",
        "depends",
        "assets",
        "description",
        "summary",
        "external_dependencies",
        "demo",
    ]

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
    # mainteners: List[str] = []
    installable: bool = True
    auto_install: bool = False
    application: bool = False

    @computed_field(return_type=str)
    @property
    def version(self):
        """Computed Odoo version."""
        return f"{self.odoo_version}.{self.module_version}"

    def set_version(self, version):
        parts = version.split(".")
        self.odoo_version = ".".join(parts[:2])
        self.module_version = ".".join(parts[2:])

    def add_items(self, key, value):
        """Add items to list fields."""

        attr = getattr(self, key)
        attr += value

    def update(self, values):
        """Update with dict."""
        filtered_values = {
            k: v for k, v in values.items() if k in self.__authorized_keys__
        }
        _logger.error(filtered_values)
        return self.model_copy(update=filtered_values)

    def prepare_to_save(self):
        """Prepare ordered content to save."""
        data = self.model_dump(exclude={"odoo_version", "module_version"})

        res = OrderedDict([(key, data.get(key)) for key in self.__keys__])
        _logger.debug(res)
        # return json.loads(json.dumps(res))
        return dict(res)


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
