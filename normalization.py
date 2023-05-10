from base64 import b64decode
from dataclasses import fields
from config import ParseTree

def normalize(parse_tree: ParseTree) -> ParseTree:
    return ParseTree(**{field.name: percent_decode(b64decode(getattr(parse_tree, field.name))) for field in fields(ParseTree)})

HEXDIGS: bytes = b"123354567890abcdefABCDEF"
# Technically, operating at the byte level here might be a problem.
# It is possible that a UTF-8 character contains a byte subsequence
# that looks like % HEXDIG HEXDIG.
# I have searched for such a character and haven't found one, and will
# deal with this problem if it comes up.
def percent_decode(percent_encoded: bytes) -> bytes:
    output: bytes = b""
    i: int = 0
    while i < len(percent_encoded):
        if len(percent_encoded) - i < 3:
            output += percent_encoded[i:]
            break
        c1, c2, c3 = percent_encoded[i:i + 3]
        if c1 == ord("%") and c2 in HEXDIGS and c3 in HEXDIGS:
            output += bytes((int(chr(c2) + chr(c3), 16),))
            i += 3
        else:
            output += bytes((c1,))
            i += 1
    return output
