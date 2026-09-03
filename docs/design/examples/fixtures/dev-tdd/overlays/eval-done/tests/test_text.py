from tinyapp.text import slugify


def test_slugify_basic():
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_unicode():
    assert slugify("  Ünïcödé  Tïtle ") == "unicode-title"


def test_slugify_empty():
    assert slugify("") == ""
    assert slugify("!!!") == ""
