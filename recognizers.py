# This program contains recognizers for some of the characters classes and expressions used in URL parsing.
# It's not used in anything, but it can be helpful to have around.


def is_scheme(s: str) -> bool:
    """RFC3986, RFC3987: scheme = ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )"""
    return (
        s != ""
        and s.isascii()
        and s[0].isalpha()
        and all(c.isalnum() or c in "+-." for c in s[1:])
    )


def is_reg_name(s: str) -> bool:
    """RFC3986: reg-name = *( unreserved / pct-encoded / sub-delims )"""
    return all(
        is_unreserved(c) or is_sub_delim(c) or is_pct_encoded(s[i : i + 3])
        for i, c in enumerate(s)
    )


def is_ireg_name(s: str) -> bool:
    """RFC3987: ireg-name = *( iunreserved / pct-encoded / sub-delims )"""
    return all(
        is_iunreserved(c) or is_sub_delim(c) or is_pct_encoded(s[i : i + 3])
        for i, c in enumerate(s)
    )


def is_unreserved(c: str) -> bool:
    """RFC3986: unreserved = ALPHA / DIGIT / "-" / "." / "_" / "~" """
    assert len(c) == 1
    return c.isascii() and (c.isalnum() or c in "-._~")


def is_iunreserved(c: str) -> bool:
    """RFC3987: iunreserved = ALPHA / DIGIT / "-" / "." / "_" / "~" / ucschar"""
    assert len(c) == 1
    return is_unreserved(c) or is_ucschar(c)


def is_ucschar(c: str) -> bool:
    """RFC3987: ucschar = %xA0-D7FF / %xF900-FDCF / %xFDF0-FFEF / %x10000-1FFFD / %x20000-2FFFD / %x30000-3FFFD / %x40000-4FFFD / %x50000-5FFFD / %x60000-6FFFD / %x70000-7FFFD / %x80000-8FFFD / %x90000-9FFFD / %xA0000-AFFFD / %xB0000-BFFFD / %xC0000-CFFFD / %xD0000-DFFFD / %xE1000-EFFFD"""
    assert len(c) == 1
    code_point: int = ord(c)
    return (
        code_point in range(0xA0, 0xD7FF + 1)
        or code_point in range(0xF900, 0xFDCF + 1)
        or code_point in range(0xFDF0, 0xFFEF + 1)
        or code_point in range(0x10000, 0x1FFFD + 1)
        or code_point in range(0x20000, 0x2FFFD + 1)
        or code_point in range(0x30000, 0x3FFFD + 1)
        or code_point in range(0x40000, 0x4FFFD + 1)
        or code_point in range(0x50000, 0x5FFFD + 1)
        or code_point in range(0x60000, 0x6FFFD + 1)
        or code_point in range(0x70000, 0x7FFFD + 1)
        or code_point in range(0x80000, 0x8FFFD + 1)
        or code_point in range(0x90000, 0x9FFFD + 1)
        or code_point in range(0xA0000, 0xAFFFD + 1)
        or code_point in range(0xB0000, 0xBFFFD + 1)
        or code_point in range(0xC0000, 0xCFFFD + 1)
        or code_point in range(0xD0000, 0xDFFFD + 1)
        or code_point in range(0xE1000, 0xEFFFD + 1)
    )


def is_sub_delim(c: str) -> bool:
    """RFC3986, RFC3987: sub-delims = "!" / "$" / "&" / "'" / "(" / ")" / "*" / "+" / "," / ";" / "=" """
    assert len(c) == 1
    return c in "!$&'()*+,;="


def is_pct_encoded(s: str) -> bool:
    """RFC3986, RFC3987: pct-encoded = "%" HEXDIG HEXDIG"""
    """ WHATWG: A percent-encoded byte is U+0025 (%), followed by two ASCII hex digits. Sequences of percent-encoded bytes, percent-decoded, should not cause UTF-8 decode without BOM or fail to return failure. """
    # Note that these are actually in conflict, because HEXDIG is defined to be [0-9A-F], so lowercase hexdigs cause problems.
    return (
        len(s) == 3
        and s[0] == "%"
        and s[1] in "01234567890abcdefABCDEF"
        and s[2] in "01234567890abcdefABCDEF"
    )


def is_userinfo(s: str) -> bool:
    """RFC3986: userinfo = *( unreserved / pct-encoded / sub-delims / ":" )"""
    return all(
        is_unreserved(c) or is_pct_encoded(s[i : i + 3]) or is_sub_delim(c) or c == ":"
        for i, c in enumerate(s)
    )


def is_iuserinfo(s: str) -> bool:
    """iuserinfo = *( iunreserved / pct-encoded / sub-delims / ":" )"""
    return all(
        is_iunreserved(c) or is_pct_encoded(s[i : i + 3]) or is_sub_delim(c) or c == ":"
        for i, c in enumerate(s)
    )


def is_surrogate(c: str) -> bool:
    """WHATWG: A surrogate is a code point that is in the range U+D800 to U+DFFF, inclusive."""
    assert len(c) == 1
    return ord(c) in range(0xD800, 0xDFFF + 1)


def is_noncharacter(c: str) -> bool:
    """WHATWG: A noncharacter is a code point that is in the range U+FDD0 to U+FDEF, inclusive, or U+FFFE, U+FFFF, U+1FFFE, U+1FFFF, U+2FFFE, U+2FFFF, U+3FFFE, U+3FFFF, U+4FFFE, U+4FFFF, U+5FFFE, U+5FFFF, U+6FFFE, U+6FFFF, U+7FFFE, U+7FFFF, U+8FFFE, U+8FFFF, U+9FFFE, U+9FFFF, U+AFFFE, U+AFFFF, U+BFFFE, U+BFFFF, U+CFFFE, U+CFFFF, U+DFFFE, U+DFFFF, U+EFFFE, U+EFFFF, U+FFFFE, U+FFFFF, U+10FFFE, or U+10FFFF."""
    assert len(c) == 1
    return (
        ord(c) in range(0xFDD0, 0xFDEF + 1)
        or c
        in "\uFFFE\uFFFF\U0001FFFE\U0001FFFF\U0002FFFE\U0002FFFF\U0003FFFE\U0003FFFF\U0004FFFE\U0004FFFF\U0005FFFE\U0005FFFF\U0006FFFE\U0006FFFF\U0007FFFE\U0007FFFF\U0008FFFE\U0008FFFF\U0009FFFE\U0009FFFF\U000AFFFE\U000AFFFF\U000BFFFE\U000BFFFF\U000CFFFE\U000CFFFF\U000DFFFE\U000DFFFF\U000EFFFE\U000EFFFF\U000FFFFE\U000FFFFF\U0010FFFE\U0010FFFF"
    )


def is_url_code_point(c: str) -> bool:
    """WHATWG: The URL code points are ASCII alphanumeric, U+0021 (!), U+0024 ($), U+0026 (&), U+0027 ('), U+0028 LEFT PARENTHESIS, U+0029 RIGHT PARENTHESIS, U+002A (*), U+002B (+), U+002C (,), U+002D (-), U+002E (.), U+002F (/), U+003A (:), U+003B (;), U+003D (=), U+003F (?), U+0040 (@), U+005F (_), U+007E (~), and code points in the range U+00A0 to U+10FFFD, inclusive, excluding surrogates and noncharacters."""
    assert len(c) == 1
    return (
        (c.isascii() and c.isalnum())
        or c in "!$&'()*+,-./:'=?@_~"
        or (
            ord(c) in range(0x00A0, 0x10FFFD + 1)
            and not is_surrogate(c)
            and not is_noncharacter(c)
        )
    )


if __name__ == "__main__":
    import urllib.parse
    import urllib3.util
    import rfc3986
    import yarl
    import furl

    parsers = [
        # ("furl", furl.furl),
        # ("yarl", yarl.URL),
        # ("urllib", urllib.parse.urlparse),
        # ("urllib3", urllib3.util.parse_url),
        ("rfc3986", rfc3986.urlparse),
    ]
    count = 0
    for c in map(chr, range(0x110000)):
        if not is_iunreserved(c) and not is_sub_delim(
            c
        ):  # so not allowed in an ireg-name
            url = "http://" + c
            for name, parser in parsers:
                try:
                    parsed = parser(url)
                    if ("host" in dir(parsed) and parsed.host == c) or (
                        "netloc" in dir(parsed) and parsed.netloc == c
                    ):
                        count += 1
                        print(
                            "uh oh!",
                            name,
                            "says",
                            repr(url),
                            "->",
                            repr(parsed),
                            "should not have parsed!",
                        )
                        # input()
                except Exception as e:
                    if isinstance(e, KeyboardInterrupt):
                        exit()

    print(count)
