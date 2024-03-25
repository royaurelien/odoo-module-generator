import ast

# import astor

# from omg.common.logger import _logger

ODOO_MODELS = ["models", "Model", "AbstractModel", "TransientModel"]
EXCLUDE_KEYWORDS = ["default", "compute", "store", "tracking", "readonly"]


def is_model(obj):
    if not obj.bases:
        return False

    base = obj.bases[0]

    # _logger.warning(astor.to_source(base))
    # _logger.warning(astor.dump_tree(base))

    if isinstance(base, ast.Name):
        if base.id in ODOO_MODELS:
            return True

    if isinstance(base, ast.Attribute):
        # FIXME: 3 parts or more
        # tools.misc.UnquoteEvalContext
        # Attribute(value=Attribute(value=Name(id='tools'), attr='misc'), attr='UnquoteEvalContext')
        if isinstance(base.value, ast.Attribute):
            return False
        # bases=[Attribute(value=Name(id='models'), attr='Model')],
        if base.value.id in ODOO_MODELS or base.attr in ODOO_MODELS[1:]:
            return True

    return False


class GetFields(ast.NodeTransformer):
    def __init__(self):
        self._fields_count = 0
        self._fields = []

    def visit_Assign(self, node):
        assignments = [k.id for k in node.targets if isinstance(k, ast.Name)]
        if len(assignments) != 1:
            return node

        assign, value = assignments[0], node.value
        if not isinstance(value, ast.Call):
            return node

        f = value.func
        if not isinstance(f, ast.Attribute) or not isinstance(f.value, ast.Name):
            return node

        if f.value.id != "fields":
            return node

        self._fields.append(assign)

        return node


class Cleaner(ast.NodeTransformer):
    def __init__(self):
        self._arg_count = 0
        self._func = []
        self._fields_count = 0
        self._fields = []

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        self._func.append(node)

        return

    def visit_ClassDef(self, node):
        # Force class inherit to 'models.X'
        for index, base in enumerate(node.bases):
            if isinstance(base, ast.Name) and base.id in ODOO_MODELS[1:]:
                node.bases[index] = ast.Attribute("models", base.id)

        self.generic_visit(node)
        return node

    def visit_Call(self, node):  # noqa: C901
        # if isinstance(node.func, (ast.Name, ast.Subscript)):
        #     self.generic_visit(node)
        #     return node

        if not isinstance(node.func, ast.Attribute):
            return node

        if not isinstance(node.func.value, ast.Name):
            return node

        if node.func.value.id != "fields":
            return node

        keywords = {keyword.arg: keyword.value for keyword in node.keywords}
        compute = keywords.pop("compute", False)
        store = keywords.pop("store", False)

        if compute and not store:
            message = "Field previously unstored (lost value)"
        elif compute and store:
            message = "Field previously stored (retained value)"
        else:
            message = None
            keywords.pop("help", None)

        if node.args:
            attr = node.func.attr
            if len(node.args) == 1:
                first_value = node.args.pop()

                if attr in ["Many2one"] and "comodel_name" not in keywords:
                    first_arg = "comodel_name"
                elif attr in ["One2many"] and "comodel_name" not in keywords:
                    first_arg = "comodel_name"
                elif attr in ["Selection"] and "selection" not in keywords:
                    first_arg = "selection"
                else:
                    first_arg = "string"

                keywords[first_arg] = first_value

            elif len(node.args) == 2 and attr in ["Many2one", "Selection", "One2many"]:
                first_value = node.args.pop(0)
                second_value = node.args.pop(0)

                if attr in ["Many2one"]:
                    first_arg = "comodel_name"
                    second_arg = "string"
                elif attr in ["Selection"]:
                    first_arg = "selection"
                    second_arg = "string"
                elif attr in ["One2many"]:
                    if (
                        "comodel_name" not in keywords
                        and "inverse_name" not in keywords
                    ):
                        first_arg = "comodel_name"
                        second_arg = "inverse_name"

                keywords[first_arg] = first_value
                keywords[second_arg] = second_value

        if message:
            keywords["help"] = ast.Constant(message)

        node.keywords = [
            ast.keyword(k, v) for k, v in keywords.items() if k not in EXCLUDE_KEYWORDS
        ]

        self.generic_visit(node)
        return node
