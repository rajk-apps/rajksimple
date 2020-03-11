import mypackage

# from django.test import TestCase


def test_import():
    import mypackage._version

    assert mypackage.__version__ == mypackage._version.__version__
