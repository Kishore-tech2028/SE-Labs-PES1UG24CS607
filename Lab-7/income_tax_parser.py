def _to_int(s):
    """Convert a string of plain ASCII digits to int, otherwise return None."""
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not (s.isascii() and s.isdigit()):
        return None
    try:
        return int(s)
    except ValueError:  # e.g. absurdly long digit strings
        return None


def clean_pan(pan):
    """
    Removes spaces from a PAN and upper-cases it.
    Returns None if pan is not a string.
    """
    if not isinstance(pan, str):
        return None
    return "".join(pan.split()).upper()


def parse_amount(text):
    """
    Converts an amount such as 'Rs 12,50,000' into an int.
    Returns None for non-strings or anything that is not a plain number.
    """
    if not isinstance(text, str):
        return None
    text = text.replace('Rs', '').replace(',', '')
    return _to_int("".join(text.split()))


def parse_tax_slab(line):
    """
    Parses 'LOW-HIGH:RATE' into a (low, high, rate) tuple.
    Returns None if the line is not in that exact format.
    """
    if not isinstance(line, str):
        return None
    parts = line.split(':')
    if len(parts) != 2:
        return None
    limits = parts[0].split('-')
    if len(limits) != 2:
        return None
    low, high, rate = _to_int(limits[0]), _to_int(limits[1]), _to_int(parts[1])
    if low is None or high is None or rate is None or low > high:
        return None
    return low, high, rate


def main():
    print("==== Running clean_pan ====")
    value = input("Enter a PAN (e.g. abcde 1234f): ")
    print("Cleaned PAN:", clean_pan(value))

    print("\n==== Running parse_amount ====")
    value = input("Enter an amount (e.g. Rs 12,50,000): ")
    print("Amount in rupees:", parse_amount(value))

    print("\n==== Running parse_tax_slab ====")
    value = input("Enter a tax slab as LOW-HIGH:RATE (e.g. 250000-500000:5): ")
    print("Tax slab (low, high, rate):", parse_tax_slab(value))


if __name__ == "__main__":
    main()
