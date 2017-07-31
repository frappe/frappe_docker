import pytest

# Global objects under tests

@pytest.fixture
def Workbook():
    """Workbook Class"""
    from openpyxl import Workbook
    return Workbook


@pytest.fixture
def Worksheet():
    """Worksheet Class"""
    from openpyxl.worksheet import Worksheet
    return Worksheet


# Global fixtures


### Markers ###

def pytest_runtest_setup(item):
    if isinstance(item, item.Function):
        try:
            from PIL import Image
        except ImportError:
            Image = False
        if item.get_marker("pil_required") and Image is False:
            pytest.skip("PIL must be installed")
        elif item.get_marker("pil_not_installed") and Image:
            pytest.skip("PIL is installed")
        elif item.get_marker("not_py33"):
            pytest.skip("Ordering is not a given in Python 3")
        elif item.get_marker("lxml_required"):
            from openpyxl import LXML
            if not LXML:
                pytest.skip("LXML is required for some features such as schema validation")
        elif item.get_marker("lxml_buffering"):
            from lxml.etree import LIBXML_VERSION
            if LIBXML_VERSION < (3, 4, 0, 0):
                pytest.skip("LXML >= 3.4 is required")
        elif item.get_marker("no_lxml"):
            from openpyxl import LXML
            if LXML:
                pytest.skip("LXML has a different interface")
        elif item.get_marker("numpy_required"):
            from openpyxl import NUMPY
            if not NUMPY:
                pytest.skip("Numpy must be installed")
        elif item.get_marker("pandas_required"):
            from openpyxl import PANDAS
            if not PANDAS:
                pytest.skip("Pandas must be installed")
