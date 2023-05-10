import sys
import io

from diff_fuzz import run_executables
from config import TARGET_CONFIGS
from normalization import normalize

def main(input_file: io.BufferedReader) -> None:
    fingerprint, statuses, parse_trees = run_executables(input_file.read())
    for tc, status, parse_tree in zip(TARGET_CONFIGS, statuses, map(normalize, parse_trees)):
        print(tc.executable)
        print(status)
        print(parse_tree)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <file_to_interpret>")

    main(open(sys.argv[1], "rb"))
