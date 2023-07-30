import csv
import os

from omg.core.models import IrModelAccess

IR_MODEL_ACCESS_FILENAME = "ir.model.access.csv"


class Security:
    def __init__(self):
        self.ir_model_access = None

    def new_model_access(self, lines):
        self.ir_model_access = IrModelAccess(lines=lines)

    def generate_ir_model_access(self, path):
        filepath = os.path.join(path, "security", IR_MODEL_ACCESS_FILENAME)
        header = self.ir_model_access.__fields__
        data = self.ir_model_access.dict()["lines"]

        with open(filepath, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=header)
            writer.writeheader()
            writer.writerows(data)
