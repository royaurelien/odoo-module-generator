import xml.etree.ElementTree as ET
from pprint import pprint

from omg.core.tools import generate

import os


def extract(item):
    vals = item.attrib

    if not "name" in vals:
        # print(item.text)
        return (False, False)
    key = vals.pop("name")

    if len(vals):
        values = list(vals.values())
        if len(values) == 1:
            values = values[0]
    else:
        values = item.text

    return (key, values)


def escape(var):
    return f'"{var}"'


def parse_xml_from_path(path):
    tree = ET.parse(path)
    root = tree.getroot()

    fields = {}

    for record in root:
        model = record.attrib.get("model")

        data = dict(extract(child) for child in record.iter() if child.tag == "field")
        name = data.get("name")
        fields[name] = data

    fields_by_models = {}

    for name, attrs in fields.items():
        model = attrs["model"]
        ttype = attrs.get("ttype").capitalize()
        args = {"string": escape(attrs.get("field_description"))}

        if ttype == "Selection":
            args["selection"] = attrs.get("selection")
        elif ttype == "Many2one":
            args["comodel_name"] = escape(attrs.get("relation"))

        if attrs["related"] != "False":
            args["related"] = escape(attrs.get("related"))

        args = [f"{k}={v}" for k, v in args.items()]
        field = f"{name} = fields.{ttype}({', '.join(args)},)"

        fields_by_models.setdefault(model, [])
        fields_by_models[model].append(field)

    return fields_by_models


def generate_model(path, name, fields):
    filename = name.replace(".", "_")
    filepath = os.path.join(path, filename)
    classname = "".join(map(str.capitalize, name.split(".")))

    vals = {
        "name": name,
        "inherit": name,
        "classname": classname,
        "fields": fields,
    }

    return generate("model.jinja2", vals, filepath)
