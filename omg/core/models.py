# -*- coding: utf-8 -*-
#!/bin/python3


from collections import namedtuple

File = namedtuple(
    "File",
    ["name", "path", "content"],
)


class FakeModel(object):
    def __init__(self):
        self.name = ""
        self.fields = dict()

    @property
    def field(self):
        return self.fields[next(iter(self.fields))]
