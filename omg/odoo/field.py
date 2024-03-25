class Field:
    def __init__(self, ttype: str, definition: str = None, **kwargs: dict):
        self.ttype = ttype
        self.definition = definition
        self.args = []
        self.keywords = {}

        # args, keywords
        self.__dict__.update(kwargs)
        self.sanitize()

    def __repr__(self) -> str:
        return f"<Field ({self.ttype}): {self.name}>"
