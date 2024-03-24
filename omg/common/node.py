import ast
import astor

ODOO_MODELS = ["models", "Model", "AbstractModel", "TransientModel"]


class Cleaner(ast.NodeTransformer):

    def __init__(self):
        self._arg_count = 0
        self._func = []

    def visit_FunctionDef(self, node):
        # node.name = "method_name"
        # print(node.name)
        self.generic_visit(node)
        # return node
        self._func.append(node)

        return

    # def visit_arg(self, node):
    #     print(node.arg)

    #     node.arg = "arg_{}".format(self._arg_count)
    #     self._arg_count += 1
    #     self.generic_visit(node)
    #     return node

    def visit_ClassDef(self, node):
        # Force class inherit to 'models.X'
        for index, base in enumerate(node.bases):
            if isinstance(base, ast.Name) and base.id in ODOO_MODELS[1:]:
                node.bases[index] = ast.Attribute("models", base.id)

        self.generic_visit(node)
        return node

    def visit_Call(self, node):

        if isinstance(node.func, (ast.Name, ast.Subscript)):
            self.generic_visit(node)
            return node

        # id = node.func.value.id
        attr = node.func.attr

        keywords = [keyword.arg for keyword in node.keywords]

        if node.args:
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

                node.keywords.append(ast.keyword(first_arg, first_value))

            elif len(node.args) == 2 and attr in ["Many2one", "Selection"]:
                first_value = node.args.pop()
                second_value = node.args.pop()

                if attr in ["Many2one"]:
                    first_arg = "comodel_name"
                    second_arg = "string"
                elif attr in ["Selection"]:
                    first_arg = "selection"
                    second_arg = "string"

                node.keywords.append(ast.keyword(first_arg, first_value))
                node.keywords.append(ast.keyword(second_arg, second_value))

        exclude = ["default", "compute", "help", "store"]
        node.keywords = [
            keyword for keyword in node.keywords if keyword.arg not in exclude
        ]

        self.generic_visit(node)
        # print(astor.dump_tree(node))
        # print(astor.to_source(node))
        return node
