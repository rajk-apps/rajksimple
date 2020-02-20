import mydjangoapp

# from django.test import TestCase


def test_import():
    import mydjangoapp._version

    assert mydjangoapp.__version__ == mydjangoapp._version.__version__
