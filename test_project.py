from project import is_name, page_count, average
import enchant


def test_is_name():
    d = enchant.Dict("es_ES")
    assert is_name("PANEL 1", d) == False
    assert is_name("JUAN", d) == True


def test_page_count():
    # Pasa una lista simulada de lineas
    lines = ["PAGE 1", "Un texto cualquiera", "page 2"]
    assert page_count(lines) == 2


def test_average():
    assert average(10, 2) == 5.0
