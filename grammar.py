import re
from re._parser import (  # type: ignore
    parse as re_parse,
    IN,
    CATEGORY_DIGIT,
    CATEGORY_NOT_DIGIT,
    CATEGORY_WORD,
    CATEGORY_NOT_WORD,
    CATEGORY_SPACE,
    CATEGORY_NOT_SPACE,
    SubPattern,
    LITERAL,
    NOT_LITERAL,
    MAX_REPEAT,
    SUBPATTERN,
    NEGATE,
    RANGE,
    CATEGORY,
    BRANCH,
    ANY,
)
from re._constants import _NamedIntConstant as RegexConstant  # type: ignore
import random
from typing import Dict, FrozenSet, Any, Iterable, Set

# A grammar maps rule names either a string or a sequence of rule names
# A terminal always maps to a regex
# A nonterminal always maps to a list of rule names

# unreserved = ALPHA / DIGIT / "-" / "." / "_" / "~"
UNRESERVED_PAT: str = r"(?:[A-Za-z0-9\-\._~])"

# pct-encoded = "%" HEXDIG HEXDIG
PCT_ENCODED_PAT: str = r"(?:%[A-F0-9][A-F0-9])"

# sub-delims = "!" / "$" / "&" / "'" / "(" / ")" / "*" / "+" / "," / ";" / "="
SUB_DELIMS_PAT: str = r"(?:[!\$&'\(\)\*\+,;=])"

# pchar = unreserved / pct-encoded / sub-delims / ":" / "@"
PCHAR_PAT: str = rf"(?:{UNRESERVED_PAT}|{PCT_ENCODED_PAT}|{SUB_DELIMS_PAT}|:|@)"

# query = *( pchar / "/" / "?" )
QUERY_PAT: str = rf"(?P<query>(?:{PCHAR_PAT}|/|\?)*)"
QUERY_RE: re.Pattern = re.compile(QUERY_PAT)

# fragment = *( pchar / "/" / "?" )
FRAGMENT_PAT: str = rf"(?P<fragment>(?:{PCHAR_PAT}|/|\?)*)"
FRAGMENT_RE: re.Pattern = re.compile(FRAGMENT_PAT)

# scheme = ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )
SCHEME_PAT: str = r"(?P<scheme>[A-Za-z][A-Za-z0-9\+\-\.]*)"
SCHEME_RE: re.Pattern = re.compile(SCHEME_PAT)

# segment = *pchar
SEGMENT_PAT: str = rf"(?:{PCHAR_PAT}*)"

# segment-nz = 1*pchar
SEGMENT_NZ_PAT: str = rf"(?:{PCHAR_PAT}+)"

# segment-nz-nc = 1*( unreserved / pct-encoded / sub-delims / "@" )
SEGMENT_NZ_NC_PAT: str = rf"(?:(?:{UNRESERVED_PAT}|{PCT_ENCODED_PAT}|{SUB_DELIMS_PAT}|@)+)"

# path-absolute = "/" [ segment-nz *( "/" segment ) ]
PATH_ABSOLUTE_PAT: str = rf"(?P<path_absolute>/(?:{SEGMENT_NZ_PAT}(?:/{SEGMENT_PAT})*)?)"
PATH_ABSOLUTE_RE: re.Pattern = re.compile(PATH_ABSOLUTE_PAT)

# path-empty = 0<pchar>
PATH_EMPTY_PAT: str = r"(?P<path_empty>)"
PATH_EMPTY_RE: re.Pattern = re.compile(PATH_EMPTY_PAT)

# path-rootless = segment-nz *( "/" segment )
PATH_ROOTLESS_PAT: str = rf"(?P<path_rootless>{SEGMENT_NZ_PAT}(?:/{SEGMENT_PAT})*)"
PATH_ROOTLESS_RE: re.Pattern = re.compile(PATH_ROOTLESS_PAT)

# path-abempty = *( "/" segment )
PATH_ABEMPTY_PAT: str = rf"(?P<path_abempty>(?:/{SEGMENT_PAT})*)"
PATH_ABEMPTY_RE: re.Pattern = re.compile(PATH_ABEMPTY_PAT)

# path-noscheme = segment-nz-nc *( "/" segment )
PATH_NOSCHEME_PAT: str = rf"(?P<path_noscheme>{SEGMENT_NZ_NC_PAT}(?:/{SEGMENT_PAT})*)"
PATH_NOSCHEME_RE: re.Pattern = re.compile(PATH_NOSCHEME_PAT)

# userinfo = *( unreserved / pct-encoded / sub-delims / ":" )
USERINFO_PAT: str = rf"(?P<userinfo>(?:{UNRESERVED_PAT}|{PCT_ENCODED_PAT}|{SUB_DELIMS_PAT}|:)*)"
USERINFO_RE: re.Pattern = re.compile(USERINFO_PAT)

# dec-octet = DIGIT                 ; 0-9
#           / %x31-39 DIGIT         ; 10-99
#           / "1" 2DIGIT            ; 100-199
#           / "2" %x30-34 DIGIT     ; 200-249
#           / "25" %x30-35          ; 250-255
DEC_OCTET_PAT: str = r"(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])"

# IPv4address = dec-octet "." dec-octet "." dec-octet "." dec-octet
IPV4ADDRESS_PAT: str = rf"(?:{DEC_OCTET_PAT}\.{DEC_OCTET_PAT}\.{DEC_OCTET_PAT}\.{DEC_OCTET_PAT})"
IPV4ADDRESS_RE: re.Pattern = re.compile(IPV4ADDRESS_PAT)

# h16 = 1*4HEXDIG
H16_PAT: str = r"(?:[0-9A-F]{1,4})"

# ls32 = ( h16 ":" h16 ) / IPv4address
LS32_PAT: str = rf"(?:{H16_PAT}:{H16_PAT}|{IPV4ADDRESS_PAT})"

# IPv6address =                            6( h16 ":" ) ls32
#             /                       "::" 5( h16 ":" ) ls32
#             / [               h16 ] "::" 4( h16 ":" ) ls32
#             / [ *1( h16 ":" ) h16 ] "::" 3( h16 ":" ) ls32
#             / [ *2( h16 ":" ) h16 ] "::" 2( h16 ":" ) ls32
#             / [ *3( h16 ":" ) h16 ] "::"    h16 ":"   ls32
#             / [ *4( h16 ":" ) h16 ] "::"              ls32
#             / [ *5( h16 ":" ) h16 ] "::"              h16
#             / [ *6( h16 ":" ) h16 ] "::"
IPV6ADDRESS_PAT: str = (
    "(?:"
    + r"|".join(
        (
            rf"(?:{H16_PAT}:){{6}}{LS32_PAT}",
            rf"::(?:{H16_PAT}:){{5}}{LS32_PAT}",
            rf"(?:{H16_PAT})?::(?:{H16_PAT}:){{4}}{LS32_PAT}",
            rf"(?:(?:{H16_PAT}:){{0,1}}{H16_PAT})?::(?:{H16_PAT}:){{3}}{LS32_PAT}",
            rf"(?:(?:{H16_PAT}:){{0,2}}{H16_PAT})?::(?:{H16_PAT}:){{2}}{LS32_PAT}",
            rf"(?:(?:{H16_PAT}:){{0,3}}{H16_PAT})?::(?:{H16_PAT}:){{1}}{LS32_PAT}",
            rf"(?:(?:{H16_PAT}:){{0,4}}{H16_PAT})?::{LS32_PAT}",
            rf"(?:(?:{H16_PAT}:){{0,5}}{H16_PAT})?::{H16_PAT}",
            rf"(?:(?:{H16_PAT}:){{0,6}}{H16_PAT})?::",
        )
    )
    + ")"
)
IPV6ADDRESS_RE: re.Pattern = re.compile(IPV6ADDRESS_PAT)

# IPvFuture = "v" 1*HEXDIG "." 1*( unreserved / sub-delims / ":" )
IPVFUTURE_PAT: str = rf"(?:v[0-9A-F]+\.(?:{UNRESERVED_PAT}|{SUB_DELIMS_PAT}|:)+)"
IPVFUTURE_RE: re.Pattern = re.compile(IPVFUTURE_PAT)

# IP-literal = "[" ( IPv6address / IPvFuture  ) "]"
IP_LITERAL_PAT: str = rf"(?:\[(?:{IPV6ADDRESS_PAT}|{IPVFUTURE_PAT})\])"
IP_LITERAL_RE: re.Pattern = re.compile(IPV6ADDRESS_PAT)

# reg-name = *( unreserved / pct-encoded / sub-delims )
REG_NAME_PAT: str = rf"(?:(?:{UNRESERVED_PAT}|{PCT_ENCODED_PAT}|{SUB_DELIMS_PAT})*)"
REG_NAME_RE: re.Pattern = re.compile(REG_NAME_PAT)

# host = IP-literal / IPv4address / reg-name
HOST_PAT: str = rf"(?P<host>{IP_LITERAL_PAT}|{IPV4ADDRESS_PAT}|{REG_NAME_PAT})"
HOST_RE: re.Pattern = re.compile(HOST_PAT)

# port = *DIGIT
# PORT_PAT: str = r"(?P<port>[0-9]*)"
# WHATWG version (fits in uint16_t):
PORT_PAT: str = r"(?P<port>0*[1-9]?[0-9]?[0-9]?[0-9]?|0*6553[0-5]|0*655[0-2][0-9]|0*65[0-4][0-9][0-9]|0*6[0-4][0-9][0-9][0-9])"
PORT_RE: re.Pattern = re.compile(PORT_PAT)

# authority = [ userinfo "@" ] host [ ":" port ]
AUTHORITY_PAT: str = rf"(?:(?:{USERINFO_PAT}@)?{HOST_PAT}(?::{PORT_PAT})?)"
AUTHORITY_RE: re.Pattern = re.compile(AUTHORITY_PAT)

# hier-part = "//" authority path-abempty
#           / path-absolute
#           / path-rootless
#           / path-empty
HIER_PART_PAT: str = (
    rf"(?:(?://{AUTHORITY_PAT}{PATH_ABEMPTY_PAT})|{PATH_ABSOLUTE_PAT}|{PATH_ROOTLESS_PAT}|{PATH_EMPTY_PAT})"
)
HIER_PART_RE: re.Pattern = re.compile(HIER_PART_PAT)

# URI = scheme ":" hier-part [ "?" query ] [ "#" fragment ]
URI_PAT: str = rf"(?:{SCHEME_PAT}:{HIER_PART_PAT}(?:\?{QUERY_PAT})?(?:#{FRAGMENT_PAT})?)"
URI_RE: re.Pattern = re.compile(URI_PAT)

# relative-part = "//" authority path-abempty
#                  / path-absolute
#                  / path-noscheme
#                  / path-empty
REL_PART_PAT: str = (
    rf"(?:(?://{AUTHORITY_PAT}{PATH_ABEMPTY_PAT})|{PATH_ABSOLUTE_PAT}|{PATH_NOSCHEME_PAT}|{PATH_EMPTY_PAT})"
)
REL_PART_RE: re.Pattern = re.compile(REL_PART_PAT)

REL_REF_EXT: str = "_rel"

# relative-ref  = relative-part [ "?" query ] [ "#" fragment ]
REL_REF_PAT: str = rf"(?:{REL_PART_PAT}(?:\?{QUERY_PAT})?(?:#{FRAGMENT_PAT})?)".replace(
    ">", f"{REL_REF_EXT}>"
)
REL_REF_RE: re.Pattern = re.compile(REL_REF_PAT)

# URI-reference = URI / relative-ref
URI_REF_PAT = rf"^(?:{URI_PAT}|{REL_REF_PAT})$"
URI_REF_RE: re.Pattern = re.compile(URI_REF_PAT.encode("ASCII"))

grammar_re = URI_REF_RE
grammar_dict: Dict[str, bytes] = {
    "scheme": SCHEME_PAT.encode("ASCII"),
    "userinfo": USERINFO_PAT.encode("ASCII"),
    "host": HOST_PAT.encode("ASCII"),
    "port": PORT_PAT.encode("ASCII"),
    "path_abempty": PATH_ABEMPTY_PAT.encode("ASCII"),
    "path_absolute": PATH_ABSOLUTE_PAT.encode("ASCII"),
    "path_rootless": PATH_ROOTLESS_PAT.encode("ASCII"),
    "path_empty": PATH_EMPTY_PAT.encode("ASCII"),
    "path_noscheme": PATH_NOSCHEME_PAT.encode("ASCII"),
    "query": QUERY_PAT.encode("ASCII"),
    "fragment": FRAGMENT_PAT.encode("ASCII"),
}

for reg_rule_name in grammar_dict.copy():
    grammar_dict[f"{reg_rule_name}{REL_REF_EXT}"] = grammar_dict[reg_rule_name]


# This relies on the internal workings of the re module, so don't be surprised if it crashes or doesn't
# work on versions of Python other than 3.11.3.
# I do not want to support Unicode, because it would be way harder. This only works for bytes.
# If you want something that supports Unicode, consider using hypothesis.strategies.from_regex.
# This also does not support \A, \Z, \b, ^, and $.

WORD_CHARSET: FrozenSet[int] = frozenset(
    b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz\xaa\xb2\xb3\xb5\xb9\xba\xbc\xbd\xbe\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"
)
SPACE_CHARSET: FrozenSet[int] = frozenset(b"\t\n\x0b\x0c\r\x1c\x1d\x1e\x1f \x85\xa0")
DIGIT_CHARSET: FrozenSet[int] = frozenset(b"0123456789")
ALL_CHARSET: FrozenSet[int] = frozenset(range(256))


def category_to_charset(category: RegexConstant) -> FrozenSet[int]:
    if category == CATEGORY_DIGIT:
        return DIGIT_CHARSET
    if category == CATEGORY_NOT_DIGIT:
        return negate_charset(DIGIT_CHARSET)
    if category == CATEGORY_WORD:
        return WORD_CHARSET
    if category == CATEGORY_NOT_WORD:
        return negate_charset(WORD_CHARSET)
    if category == CATEGORY_SPACE:
        return SPACE_CHARSET
    if category == CATEGORY_NOT_SPACE:
        return negate_charset(SPACE_CHARSET)
    raise NotImplementedError(f"I don't know how to generate examples of {category}")


def negate_charset(charset: Iterable[int]) -> FrozenSet[int]:
    return ALL_CHARSET - set(charset)


def helper(parse_tree: SubPattern) -> bytes:
    result: bytes = b""
    if len(parse_tree) == 0:
        return result
    curr = parse_tree[0]
    node_type: RegexConstant = curr[0]
    node_value: Any = curr[1]
    if node_type == LITERAL:
        code_point: int = node_value
        result = bytes([code_point])
    elif node_type == NOT_LITERAL:
        forbidden_code_point: int = node_value
        result = helper([(IN, [(LITERAL, b) for b in negate_charset([forbidden_code_point])])])
    elif node_type == MAX_REPEAT:
        min_reps: int = node_value[0]
        subpattern: SubPattern = node_value[2]
        for _ in range(min_reps):
            result += helper(subpattern)
    elif node_type == SUBPATTERN:
        result = helper(node_value[3])
    elif node_type == IN:
        # This needs to handle literal, range, and category
        # It also needs to handle negations for all of those
        need_to_negate: bool = False
        charset: Set[int] = set()
        for subpattern in node_value:
            if subpattern[0] == NEGATE:
                need_to_negate = not need_to_negate
            elif subpattern[0] == LITERAL:
                charset |= set([subpattern[1]])
            elif subpattern[0] == RANGE:
                charset |= set(range(subpattern[1][0], subpattern[1][1] + 1))
            elif subpattern[0] == CATEGORY:
                charset |= category_to_charset(subpattern[1])
            else:
                raise NotImplementedError(f"I don't know how to generate examples of {subpattern[0]}")
        result = bytes([random.choice(list(negate_charset(charset) if need_to_negate else charset))])
    elif node_type == BRANCH:
        result = helper(random.choice(node_value[1]))
    elif node_type == ANY:
        result = helper([(IN, [(LITERAL, b) for b in ALL_CHARSET])])
    else:
        raise NotImplementedError(f"I don't know how to generate examples of {node_type}")

    return result + helper(parse_tree[1:])


def generate_random_matching_input(pattern: bytes | str) -> bytes:
    return helper(re_parse(pattern))


def normalize_match(groupdict: dict[str, bytes | Any]) -> dict[str, bytes | Any]:
    normalized_dict: dict[str, bytes | Any] = {}
    for rule_name, rule_match in groupdict.items():
        normalized_name: str = rule_name.removesuffix(REL_REF_EXT)
        if normalized_name not in normalized_dict:
            normalized_dict[normalized_name] = rule_match
        elif normalized_dict[normalized_name] is None:
            normalized_dict[normalized_name] = rule_match
    return normalized_dict


def get_rules_to_fill(groupdict: dict[str, bytes | Any]) -> list[str]:
    rules_to_fill: list[str] = []
    if any(
        groupdict[rule_name] is not None
        for rule_name in ("path_absolute", "path_empty", "path_rootless", "path_noscheme")
    ):
        rules_to_fill = list(
            rule_name for rule_name in ("scheme", "query", "fragment") if groupdict[rule_name] is None
        )
    elif groupdict["host"] is not None:
        rules_to_fill = list(
            rule_name
            for rule_name in ("scheme", "userinfo", "port", "query", "fragment")
            if groupdict[rule_name] is None
        )
    return rules_to_fill


def is_grammar_full(groupdict: dict[str, bytes | Any]) -> bool:
    groupdict = normalize_match(groupdict)

    return len(get_rules_to_fill(groupdict)) == 0


def generate_grammar_insertion(groupdict: dict[str, bytes | Any]) -> tuple[str, bytes]:
    groupdict = normalize_match(groupdict)

    rules_to_fill: list[str] = get_rules_to_fill(groupdict)

    assert len(rules_to_fill) > 0

    rule_name = random.choice(rules_to_fill)
    return (rule_name, generate_random_matching_input(grammar_dict[rule_name]))


def serialize(groupdict: dict[str, bytes | Any]) -> bytes:
    groupdict = normalize_match(groupdict)

    serialization = b""

    serialization += groupdict["scheme"] + b":" if groupdict["scheme"] is not None else b""

    if any(groupdict[rule_name] is not None for rule_name in ("userinfo", "host", "port")):
        serialization += b"//"

    serialization += groupdict["userinfo"] + b"@" if groupdict["userinfo"] is not None else b""
    serialization += groupdict["host"] if groupdict["host"] is not None else b""
    serialization += b":" + groupdict["port"] if groupdict["port"] is not None else b""

    serialization += groupdict["path_absolute"] if groupdict["path_absolute"] is not None else b""
    serialization += groupdict["path_abempty"] if groupdict["path_abempty"] is not None else b""
    serialization += groupdict["path_rootless"] if groupdict["path_rootless"] is not None else b""
    serialization += groupdict["path_empty"] if groupdict["path_empty"] is not None else b""
    serialization += groupdict["path_noscheme"] if groupdict["path_noscheme"] is not None else b""
    serialization += b"?" + groupdict["query"] if groupdict["query"] is not None else b""
    serialization += b"#" + groupdict["fragment"] if groupdict["fragment"] is not None else b""

    return serialization
