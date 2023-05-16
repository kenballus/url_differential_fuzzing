# grammar.py
# This is a big regex that should completely match RFC3986.

import re
import warnings
from typing import Dict

from hypothesis.strategies import from_regex  # type: ignore


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
QUERY_PAT: str = rf"(?P<query>{PCHAR_PAT}|/|\?)*"
QUERY_RE: re.Pattern = re.compile(QUERY_PAT)

# fragment = *( pchar / "/" / "?" )
FRAGMENT_PAT: str = rf"(?P<fragment>{PCHAR_PAT}|/|\?)*"
FRAGMENT_RE: re.Pattern = re.compile(FRAGMENT_PAT)

# scheme = ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )
SCHEME_PAT: str = r"(?P<scheme>[A-Za-z][A-Za-z0-9\+\-\.]*)"
SCHEME_RE: re.Pattern = re.compile(SCHEME_PAT)

# segment = *pchar
SEGMENT_PAT: str = rf"(?:{PCHAR_PAT}*)"

# segment-nz = 1*pchar
SEGMENT_NZ_PAT: str = rf"(?:{PCHAR_PAT}+)"

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

# userinfo = *( unreserved / pct-encoded / sub-delims / ":" )
USERINFO_PAT: str = rf"(?P<userinfo>(?:{UNRESERVED_PAT}|{PCT_ENCODED_PAT}|{SUB_DELIMS_PAT}|:)*)"
USERINFO_RE: re.Pattern = re.compile(USERINFO_PAT)

# dec-octet = DIGIT                 ; 0-9
#           / %x31-39 DIGIT         ; 10-99
#           / "1" 2DIGIT            ; 100-199
#           / "2" %x30-34 DIGIT     ; 200-249
#           / "25" %x30-35          ; 250-255
DEC_OCTET_PAT: str = r"(?:[0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])"

# IPv4address = dec-octet "." dec-octet "." dec-octet "." dec-octet
IPV4ADDRESS_PAT: str = rf"({DEC_OCTET_PAT}\.{DEC_OCTET_PAT}\.{DEC_OCTET_PAT}\.{DEC_OCTET_PAT})"
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
    r"("
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
IPVFUTURE_PAT: str = rf"(v[0-9A-F]+\.(?:{UNRESERVED_PAT}|{SUB_DELIMS_PAT}|:)+)"
IPVFUTURE_RE: re.Pattern = re.compile(IPVFUTURE_PAT)

# IP-literal = "[" ( IPv6address / IPvFuture  ) "]"
IP_LITERAL_PAT: str = rf"(\[(?:{IPV6ADDRESS_PAT}|{IPVFUTURE_PAT})\])"
# ipvfuture is often unimplemented, so omit it:
# IP_LITERAL_PAT: str = rf"(\[{IPV6ADDRESS_PAT}\])"
IP_LITERAL_RE: re.Pattern = re.compile(IPV6ADDRESS_PAT)

# reg-name = *( unreserved / pct-encoded / sub-delims )
REG_NAME_PAT: str = rf"((?:{UNRESERVED_PAT}|{PCT_ENCODED_PAT}|{SUB_DELIMS_PAT})*)"
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
AUTHORITY_PAT: str = rf"((?:{USERINFO_PAT}@)?{HOST_PAT}(:{PORT_PAT})?)"
AUTHORITY_RE: re.Pattern = re.compile(AUTHORITY_PAT)

# hier-part = "//" authority path-abempty
#           / path-absolute
#           / path-rootless
#           / path-empty
HIER_PART_PAT: str = (
    rf"((?://{AUTHORITY_PAT}{PATH_ABEMPTY_PAT})|{PATH_ABSOLUTE_PAT}|{PATH_ROOTLESS_PAT}|{PATH_EMPTY_PAT})"
)
HIER_PART_RE: re.Pattern = re.compile(HIER_PART_PAT)

# URI = scheme ":" hier-part [ "?" query ] [ "#" fragment ]
URI_PAT: str = rf"({SCHEME_PAT}:{HIER_PART_PAT}(?:\?{QUERY_PAT})?(?:#{FRAGMENT_PAT})?)"
URI_RE: re.Pattern = re.compile(URI_PAT)

grammar_re = URI_RE
grammar_dict: Dict[str, str] = {
    "query": QUERY_PAT,
    "fragment": FRAGMENT_PAT,
    "scheme": SCHEME_PAT,
    "path_absolute": PATH_ABSOLUTE_PAT,
    "path_empty": PATH_EMPTY_PAT,
    "path_rootless": PATH_ROOTLESS_PAT,
    "path_abempty": PATH_ABEMPTY_PAT,
    "userinfo": USERINFO_PAT,
    "host": HOST_PAT,
    "port": PORT_PAT,
}


def generate_random_matching_input(pattern: str) -> str:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return from_regex(r"\A" + pattern + r"\Z").example()
