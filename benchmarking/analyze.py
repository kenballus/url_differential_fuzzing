import os
import sys
import json
import shutil
import itertools
import uuid
from pathlib import PosixPath

import matplotlib.pyplot as plt  # type: ignore
import numpy as np

RESULTS_DIR = "../results"
REPORT_DIR = "reports"
ANALYSES_DIR = "analyses"

working_dir: str = os.path.dirname(__file__)
parent_dir: str = os.path.dirname(working_dir)
sys.path.append(parent_dir)

os.chdir(parent_dir)
from diff_fuzz import trace_batch, fingerprint_t  # type: ignore

os.chdir(working_dir)


# Check that necessary files exist for the given run
def assert_data(run_uuid: str):
    if not os.path.isdir(PosixPath(REPORT_DIR)):
        raise FileNotFoundError("Report Directory doesn't exist!")
    if not os.path.isfile(PosixPath(REPORT_DIR).joinpath(f"{run_uuid}_report.json")):
        raise FileNotFoundError(f"{run_uuid} doesn't have a report file!")
    if not os.path.isdir(PosixPath(RESULTS_DIR).joinpath(run_uuid)):
        raise FileNotFoundError(f"{run_uuid} doesn't have a differentials folder!")


# Plot a run onto a given axis
def plot_data(run_name: str, report_file_path: PosixPath, axis: np.ndarray):
    # Load up all the differentials from the json
    with open(report_file_path, "r", encoding="utf-8") as report_file:
        report = json.load(report_file)
    differentials = report["differentials"]
    times: list[float] = []
    generations: list[int] = []
    count: list[int] = []
    running_count: int = 0
    for differential in differentials:
        running_count += 1
        generations.append(int(differential["generation"]))
        count.append(running_count)
        times.append(float(differential["time"]))
    # Plot Things
    axis[0].plot(np.array(times), np.array(count), label=run_name)
    axis[0].set_xlabel("Time (s)")
    axis[0].set_ylabel("Bugs")
    axis[1].plot(np.array(generations), np.array(count))
    axis[1].set_xlabel("Generations")
    axis[1].set_ylabel("Bugs")


def get_fingerprint_differentials(
    differentials_folder: PosixPath,
) -> dict[fingerprint_t, bytes]:
    # Read the bugs from files
    byte_differentials: list[bytes] = []
    differentials = os.listdir(differentials_folder)
    differentials.sort(key=int)
    for diff in differentials:
        differential_file_name = differentials_folder.joinpath(diff)
        with open(differential_file_name, "rb") as differential_file:
            byte_differentials.append(differential_file.read())

    # Trace the bugs
    run_dir: PosixPath = PosixPath("/tmp").joinpath("analyzer")
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    os.mkdir(run_dir)
    os.chdir(parent_dir)
    fingerprints: list[fingerprint_t] = trace_batch(run_dir, byte_differentials)
    os.chdir(working_dir)
    shutil.rmtree(run_dir)

    # Record
    fingerprints_bytes = {}
    for fingerprint, byte_differential in zip(fingerprints, byte_differentials):
        fingerprints_bytes[fingerprint] = byte_differential
    return fingerprints_bytes


# Given dictionaries of fingerprints in each run and the bytes those fingerprints correspond to
def summarize_common_bugs(
    runs_to_analyze: set[tuple[str, str]], analysis_file_path: PosixPath, analysis_name: str
):
    run_differentials: dict[str, dict[fingerprint_t, bytes]] = {}
    for run_name, run_uuid in runs_to_analyze:
        run_differentials[run_name] = get_fingerprint_differentials(PosixPath(RESULTS_DIR).joinpath(run_uuid))
    # Setup analysis file
    with open(analysis_file_path, "wb") as analysis_file:
        analysis_file.write(f"Analysis: {analysis_name}\n".encode("utf-8"))
    # Get list of combos from big to small
    combos = list(
        list(run for (run, _), enabled in zip(runs_to_analyze, enables) if enabled)
        for enables in itertools.product([True, False], repeat=len(runs_to_analyze))
    )
    combos.sort(key=len, reverse=True)
    seen_fingerprints: set[fingerprint_t] = set()
    for combo in combos:
        # Save combo name before editing combo
        combo_name: bytes = bytes(",".join(combo), "utf-8")
        # For each combo build list of common bugs
        if not combo:
            break
        first_run: dict[fingerprint_t, bytes] = run_differentials[combo.pop()]
        common: set[fingerprint_t] = set(first_run.keys())
        for run_name in combo:
            common = common.intersection(run_differentials[run_name].keys())
        # Take away already used bugs and mark bugs as used up
        common = common - seen_fingerprints
        seen_fingerprints = seen_fingerprints.union(common)
        # Write to the file in a readable byte format
        with open(analysis_file_path, "ab") as comparison_file:
            comparison_file.write(b"-------------------------------------------\n")
            comparison_file.write(combo_name + b"\n")
            comparison_file.write(b"Total: " + bytes(str(len(common)), "utf-8") + b"\n")
            comparison_file.write(b"-------------------------------------------\n")
            comparison_file.write(b"***")
            comparison_file.write(b"***\n***".join(first_run[x] for x in common))
            comparison_file.write(b"***\n")


def build_relative_analysis(analysis_name: str, runs_to_analyze: set[tuple[str, str]]):
    figure, axis = plt.subplots(2, 1, constrained_layout=True)
    figure.suptitle(analysis_name, fontsize=16)

    for run_name, run_uuid in runs_to_analyze:
        print(f"Analyzing: {run_name}")
        assert_data(run_uuid)
        plot_data(run_name, PosixPath(REPORT_DIR).joinpath(f"{run_uuid}_report.json"), axis)

    analysis_uuid: str = str(uuid.uuid4())
    analysis_folder: PosixPath = PosixPath(ANALYSES_DIR).joinpath(analysis_uuid)
    os.mkdir(analysis_folder)
    analysis_file_path: PosixPath = PosixPath(ANALYSES_DIR).joinpath(analysis_uuid).joinpath(analysis_uuid)

    figure.legend(loc="upper left")
    plt.savefig(analysis_file_path.with_suffix(".png"), format="png")
    plt.close()

    summarize_common_bugs(runs_to_analyze, analysis_file_path.with_suffix(".txt"), analysis_name)

    print(f"Analysis Path: {analysis_folder}")


def main():
    assert os.path.exists(RESULTS_DIR)
    assert os.path.exists(ANALYSES_DIR)
    assert os.path.exists(REPORT_DIR)

    # Check that args are correct
    assert len(sys.argv) > 3
    assert len(sys.argv) % 2 == 0

    build_relative_analysis(
        sys.argv[1], set((sys.argv[i], sys.argv[i + 1]) for i in range(2, len(sys.argv)) if i % 2 == 0)
    )


if __name__ == "__main__":
    main()
