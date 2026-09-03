"""Pre-existing test for STORY-001 criterion 1 (eval 3 overlay)."""
from tinyapp.text import slugify


def test_slugify_basic():
    assert slugify("Hello, World!") == "hello-world"
