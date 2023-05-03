from typing import Set, Iterator
import itertools

def normalize(program_stdout: bytes, encoding: str) -> bytes:
    return percent_decode(program_stdout.decode(encoding)).encode(encoding)

HEXDIGS: Set[str] = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "A", "B", "C", "D", "E", "F"}
def percent_decode(percent_encoded: str) -> str:
    if len(percent_encoded) < 3:
        return percent_encoded
    i1: Iterator[str] = iter(percent_encoded)
    i2: Iterator[str] = iter(percent_encoded); next(i2)
    i3: Iterator[str] = iter(percent_encoded); next(i3); next(i3)
    output: str = ""
    to_skip: int = 0
    for c1, c2, c3 in itertools.zip_longest(i1, i2, i3):
        if to_skip > 0:
            to_skip -= 1
        elif c1 == "%" and c2 in HEXDIGS and c3 in HEXDIGS:
            output += chr(int(c2 + c3, 16))
            to_skip = 2
        else:
            output += c1
    return output