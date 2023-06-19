import os
import sys
import json
import shutil
import itertools
from pathlib import PosixPath

import matplotlib.pyplot as plt
import numpy as np

RUNS_DIR = "runs"
ANALYSES_DIR = "analyses"

working_dir: PosixPath = os.path.dirname(__file__)
parent_dir: PosixPath = os.path.dirname(working_dir)
sys.path.append(parent_dir)

os.chdir(parent_dir)
from diff_fuzz import trace_batch, fingerprint_t

os.chdir(working_dir)


# Check that necessary files exist for the given run
def assert_data(run_name: str):
    data_folder: PosixPath = PosixPath(RUNS_DIR).joinpath(run_name)
    print(f"Analyzing: {run_name}", file=sys.stderr)
    if not os.path.isdir(data_folder):
        raise NotADirectoryError(f"{data_folder} is not a directory!")
    if not os.path.isfile(data_folder.joinpath("report.json")):
        raise FileNotFoundError(f"{data_folder} doesn't have a report file!")
    if not os.path.isdir(data_folder.joinpath("differentials")):
        raise FileNotFoundError(f"{data_folder} doesn't have a differentials folder!")


# Plot a run onto a given axis
def plot_data(run_name: str, data_folder: PosixPath, axis: np.ndarray):
    # Load up all the differentials from the json
    with open(data_folder.joinpath("report.json"), "r", encoding="utf-8") as report_file:
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
    axis[0].set_title("Bugs vs Time")
    axis[1].plot(np.array(generations), np.array(count))
    axis[1].set_title("Bugs vs Generation")


def get_fingerprint_differentials(
    data_folder: PosixPath,
) -> dict[fingerprint_t, bytes]:
    # Read the bugs from files
    byte_differentials: list[bytes] = []
    differentials_folder: PosixPath = data_folder.joinpath("differentials")
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
def summarize_common_bugs(runs_to_analyze: set[str], analysis_file_path: PosixPath):
    run_differentials: dict[str, dict[fingerprint_t, bytes]] = {}
    for run in runs_to_analyze:
        run_differentials[run] = get_fingerprint_differentials(PosixPath(RUNS_DIR).joinpath(run))
    # Clear current analysis file
    open(analysis_file_path, "wb").close()  # Clears File
    # Get list of combos from big to small
    combos = list(
        list(run for run, enabled in zip(runs_to_analyze, enables) if enabled)
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
        for run in combo:
            common = common.intersection(run_differentials[run].keys())
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


def build_relative_analysis(analysis_name: str, runs_to_analyze: set[str]):
    # Ensure relative comparisons are all present
    for run in runs_to_analyze.difference(os.listdir(RUNS_DIR)):
        raise FileNotFoundError(f"Couldn't find the data folder for: {run}")

    figure, axis = plt.subplots(2)
    figure.tight_layout(h_pad=2)

    run_differentials: dict[str, dict[fingerprint_t, bytes]] = {}

    for run in runs_to_analyze:
        assert_data(run)
        data_folder: str = PosixPath(RUNS_DIR).joinpath(run)

        plot_data(run, data_folder, axis)

        run_differentials[run] = get_fingerprint_differentials(data_folder)

    figure.legend(loc="upper left")
    analysis_file_path: PosixPath = PosixPath(ANALYSES_DIR).joinpath(analysis_name)
    plt.savefig(analysis_file_path.with_suffix(".png"), format="png")
    plt.close()

    summarize_common_bugs(runs_to_analyze, analysis_file_path.with_suffix(".txt"))


# Records all bugs from a run into a summary file
def summarize_run(data_folder: PosixPath):
    # Clear out old summary file
    summary_file_path: PosixPath = data_folder.joinpath("summary.txt")
    open(summary_file_path, "wb").close()
    # Get all differential files
    diferentials_folder_path: PosixPath = data_folder.joinpath("differentials")
    differentials = os.listdir(data_folder.joinpath("differentials"))
    try:
        differentials.sort(key=int)
    except ValueError as e:
        raise ValueError(f"Issue with {diferentials_folder_path}") from e
    for diff_file in differentials:
        # Read the differential bytes from the file
        differential_file_path = diferentials_folder_path.joinpath(diff_file)
        with open(differential_file_path, "rb") as differential_file:
            differential = differential_file.read()
        # Write them into the summary file
        with open(summary_file_path, "ab") as summary_file:
            summary_file.write(bytes(diff_file, "utf-8") + b": \n***")
            summary_file.write(differential)
            summary_file.write(b"***\n")


def mass_analysis():
    for run in os.listdir("runs"):
        try:
            assert_data(run)
            data_folder: PosixPath = PosixPath(RUNS_DIR).joinpath(run)
            figure, axis = plt.subplots(2)
            figure.tight_layout(h_pad=2)

            plot_data(run, data_folder, axis)

            plt.savefig(data_folder.joinpath("graphs.png"), format="png")
            plt.close()

            summarize_run(data_folder)
        except FileNotFoundError as e:
            print(e)


def main():
    assert os.path.exists(RUNS_DIR)
    assert os.path.exists(ANALYSES_DIR)

    if len(sys.argv) > 1:
        build_relative_analysis(sys.argv[1], set(sys.argv[2:]))
    else:
        mass_analysis()


if __name__ == "__main__":
    main()
