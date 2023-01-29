#############################################################################################
# diff_fuzz.py
# This is a wrapper around afl-showmap that does differential fuzzing a la
#   https://github.com/nezha-dt/nezha, but much slower.
# Fuzzing targets are configured in `config.py`.
#############################################################################################

import sys
import subprocess
import multiprocessing
import random
import io
import os
from pathlib import PosixPath
from enum import Enum
from typing import List, Dict, Set, FrozenSet, Tuple

from config import *

SEED_INPUTS: List[PosixPath] = list(map(SEED_DIR.joinpath, map(PosixPath, os.listdir(SEED_DIR))))

for tc in TARGET_CONFIGS:
    assert tc.executable.is_file()
assert TRACE_DIR.is_dir()
assert SEED_DIR.is_dir()
for seed in SEED_INPUTS:
    assert seed.is_file()

fingerprint_t = Tuple[FrozenSet[int], ...]


def byte_flip(s: bytes) -> bytes:
    # We never make empty files because that's boring.
    if len(s) <= 1:
        return byte_insert(s)

    index: int = random.randint(0, len(s) - 1)
    return s[:index] + bytes([random.randint(0, 255)]) + s[index + 1 :]


def byte_insert(s: bytes) -> bytes:
    index: int = random.randint(0, len(s))
    return s[:index] + bytes([random.randint(0, 255)]) + s[index:]


def probably_byte_delete(s: bytes) -> bytes:
    # Never make an empty file.
    # Empty files often cause differentials, and that's okay.
    if len(s) <= 1:
        return byte_insert(s)

    index: int = random.randint(0, len(s) - 1)
    return s[:index] + s[index + 1 :]


def mutate_input(input_filename: PosixPath) -> PosixPath:
    mutant_filename: PosixPath = PosixPath(f"inputs/{random.randint(0, 2**32-1)}.input")
    with open(mutant_filename, "wb") as f:
        f.write(
            random.choice((byte_flip, byte_insert, probably_byte_delete))(open(input_filename, "rb").read())
        )

    return mutant_filename


def parse_trace_file(trace_file: io.TextIOWrapper) -> Dict[int, int]:
    result: Dict[int, int] = {}
    for line in trace_file.readlines():
        edge, count = map(int, line.strip().split(":"))
        result[edge] = count
    return result


def get_trace_length(trace_file: io.TextIOWrapper) -> int:
    return sum(c for e, c in parse_trace_file(trace_file).items())


def get_trace_edge_set(trace_file: io.TextIOWrapper) -> FrozenSet[int]:
    return frozenset(e for e, c in parse_trace_file(trace_file).items())


def get_trace_filename(executable: PosixPath, input_file: PosixPath) -> PosixPath:
    return TRACE_DIR.joinpath(PosixPath(f"{input_file.name}.{executable.name}.trace"))


def make_command_line(target_config: TargetConfig, current_input: PosixPath) -> List[str]:
    command_line: List[str] = []
    if target_config.needs_python_afl:
        command_line.append("py-afl-showmap")
    else:
        command_line.append("afl-showmap")
    if target_config.needs_qemu:  # Enable QEMU mode, if necessary
        command_line.append("-Q")
    command_line.append("-e")  # Only care about edge coverage; ignore hit counts
    command_line += [
        "-o",
        str(get_trace_filename(target_config.executable, current_input).resolve()),
    ]
    command_line += ["-t", str(TIMEOUT_TIME)]
    command_line.append("--")
    if target_config.needs_python_afl:
        command_line.append("python3")
    command_line.append(str(target_config.executable.resolve()))
    command_line += target_config.cli_args

    return command_line


def run_executables(current_input: PosixPath) -> Tuple[fingerprint_t, Tuple[int, ...]]:
    procs: List[subprocess.Popen] = []
    for target_config in TARGET_CONFIGS:
        command_line: List[str] = make_command_line(target_config, current_input)
        procs.append(
            subprocess.Popen(
                command_line,
                stdin=open(current_input),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=target_config.env,
            )
        )

    for proc in procs:
        proc.wait()

    fingerprint: fingerprint_t = tuple(
        get_trace_edge_set(open(get_trace_filename(c.executable, current_input))) for c in TARGET_CONFIGS
    )
    return_codes: Tuple[int, ...] = tuple(proc.returncode for proc in procs)

    return fingerprint, return_codes


def main() -> None:
    if len(sys.argv) > 2:
        print(f"Usage: python3 {sys.argv[0]}", file=sys.stderr)
        sys.exit(1)

    input_queue: List[PosixPath] = SEED_INPUTS.copy()

    # One input `I` produces one trace per program being fuzzed.
    # Convert each trace to a (frozen)set of edges by deduplication.
    # Pack those sets together in a tuple.
    # This is a fingerprint of the programs' execution on the input `I`.
    # Keep these fingerprints in a set.
    # An input is worth mutation if its fingerprint is new.
    explored = set()

    generation: int = 0
    differentials: List[PosixPath] = []
    with multiprocessing.Pool(processes=multiprocessing.cpu_count() // len(TARGET_CONFIGS)) as pool:
        while len(input_queue) != 0:  # While there are still inputs to check,
            print(
                color(
                    Color.green,
                    f"Starting generation {generation}. {len(input_queue)} inputs to try.",
                )
            )
            # run the programs on the things in the input queue.
            fingerprints_and_return_codes = pool.map(run_executables, input_queue)

            mutation_candidates: List[PosixPath] = []
            rejected_candidates: List[PosixPath] = []

            for current_input, (fingerprint, return_codes) in zip(input_queue, fingerprints_and_return_codes):
                # If we found something new, mutate it and add its children to the input queue
                # If we get one program to fail while another succeeds, then we're doing good.
                if len(set(return_codes)) != 1 and fingerprint not in explored:
                    print(color(Color.blue, f"Differential: {str(current_input.resolve())}"))
                    for i, rc in enumerate(return_codes):
                        print(
                            color(
                                Color.blue,
                                f"    {str(TARGET_CONFIGS[i].executable)} returned {rc}",
                            )
                        )
                    differentials.append(current_input)
                elif fingerprint not in explored:  # We don't mutate differentials, even if they're new
                    explored.add(fingerprint)
                    # print(color(Color.yellow, f"New coverage: {str(current_input.resolve())}"))
                    mutation_candidates.append(current_input)
                else:
                    # print(color(Color.grey, f"No new coverage: {str(current_input.resolve())}"))
                    rejected_candidates.append(current_input)

            input_queue = []
            while mutation_candidates != [] and len(input_queue) < ROUGH_DESIRED_QUEUE_LEN:
                for input_to_mutate in mutation_candidates:
                    input_queue.append(mutate_input(input_to_mutate))

            for reject in rejected_candidates:
                os.remove(reject)

            print(
                color(
                    Color.green,
                    f"End of generation {generation}. {len(differentials)} total differentials and {len(mutation_candidates)} mutation candidates found.",
                )
            )

            fingerprints: List[fingerprint_t] = []
            proc_lists: List[subprocess.Popen] = []
            generation += 1

    print("Exhausted input list!")
    if differentials != []:
        print(f"Differentials:")
        print("\n".join(str(f.resolve()) for f in differentials))
    else:
        print("No differentials found! Try increasing ROUGH_DESIRED_QUEUE_LEN.")


# For pretty printing
class Color(Enum):
    red = 0
    blue = 1
    green = 2
    yellow = 3
    grey = 4
    none = 5


def color(color: Color, s: str):
    COLOR_CODES = {
        Color.red: "\033[0;31m",
        Color.blue: "\033[0;34m",
        Color.green: "\033[0;32m",
        Color.yellow: "\033[0;33m",
        Color.grey: "\033[0;90m",
        Color.none: "\033[0m",
    }
    return COLOR_CODES[color] + s + COLOR_CODES[Color.none]


if __name__ == "__main__":
    main()
