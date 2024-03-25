# import mock


from omg.core.models import DefaultListQuestion, convert_string_list_to_list

values = [
    ("item", ["item"]),
    ("aaaa, bbbb", ["aaaa", "bbbb"]),
    ("aaaa,bbbb", ["aaaa", "bbbb"]),
    ('"aaaa"', ["aaaa"]),
    ("'aaaa'", ["aaaa"]),
    ("'aaaa aa'", ["aaaa aa"]),
    ("aaaa aa", ["aaaa aa"]),
    ("aaaa aa, bbbb", ["aaaa aa", "bbbb"]),
    ("'aaaa aa', 'bbbb'", ["aaaa aa", "bbbb"]),
    (["aaaa"], ["aaaa"]),
    (("aaaa"), ["aaaa"]),
]


def test_1():
    for items in values:
        assert convert_string_list_to_list(items[0]) == items[1]


def test_2(monkeypatch):
    for index, items in enumerate(values):
        monkeypatch.setattr("builtins.input", lambda _: items[0])
        assert (
            DefaultListQuestion(question=f"Question {index} ?", default=[]).prompt()
            == items[1]
        )
