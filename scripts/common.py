import re

SUFFIX = {"LTD", "LIMITED", "PLC", "LLP", "LLC", "INC", "CIC", "CIO", "UK", "THE"}


def normalise_supplier(name):
    s = str(name).upper()
    s = s.replace("'", "").replace("’", "").replace("‘", "")
    s = s.replace("&", " AND ")
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\b(T/AS|T/A|T AS|TRADING AS)\b.*$", " ", s)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    toks = [t for t in s.split() if t not in SUFFIX]
    return " ".join(toks)
