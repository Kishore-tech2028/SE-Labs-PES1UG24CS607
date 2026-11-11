from hypothesis import given, strategies as st
from income_tax_parser import clean_pan, parse_amount, parse_tax_slab


@given(st.text() | st.none())
def test_clean_pan_no_crash(s):
    try:
        result = clean_pan(s)
        assert result is None or isinstance(result, str)
    except Exception as e:
        raise AssertionError(f"clean_pan crashed on {s!r}: {type(e).__name__}: {e}")


@given(st.text() | st.none())
def test_parse_amount_no_crash(s):
    try:
        result = parse_amount(s)
        assert result is None or isinstance(result, int)
    except Exception as e:
        raise AssertionError(f"parse_amount crashed on {s!r}: {type(e).__name__}: {e}")


@given(st.text() | st.none())
def test_parse_tax_slab_no_crash(s):
    try:
        result = parse_tax_slab(s)
        assert result is None or (isinstance(result, tuple) and len(result) == 3)
    except Exception as e:
        raise AssertionError(f"parse_tax_slab crashed on {s!r}: {type(e).__name__}: {e}")
