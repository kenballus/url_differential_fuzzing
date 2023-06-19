import os
import sys
import json
import shutil
import itertools
from pathlib import PosixPath

import matplotlib.pyplot as plt
import numpy as np

working_dir: str = os.path.dirname(__file__)
parent_dir = os.path.dirname(working_dir)
sys.path.append(parent_dir)

os.chdir(parent_dir)
from diff_fuzz import trace_batch, fingerprint_t

os.chdir(working_dir)

# Check that necessary files exist for the given run
# Returns the data folder for thre run
def get_data_folder(run_name: str) -> str:
    data_folder: str = f"runs/{run_name}"
    print(f"Analyzing: {run_name}", file=sys.stderr)
    if not os.path.isdir(data_folder):
        raise NotADirectoryError(f"{data_folder} is not a directory!")
    if not os.path.isfile(f"{data_folder}/report.json"):
        raise FileNotFoundError(f"{data_folder} doesn't have a report file!")
    if not os.path.isdir(f"{data_folder}/differentials"):
        raise FileNotFoundError(f"{data_folder} doesn't have a differentials folder!")
    return data_folder

# Plot a run onto a given axis
def plot_data(run_name: str, data_folder: str, axis: np.ndarray):
    # Load up all the differentials from the json
    with open(f"{data_folder}/report.json", "r", encoding="utf-8") as report_file:
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

# Given two empty dictionaries, returns the fingerprints in each run and the bytes those fingerprints correspond to
def record_bugs(
    run_name: str,
    data_folder: str,
    fingerprints_of_runs: dict[str, list[fingerprint_t]],
    fingerprints_to_bytes: dict[fingerprint_t, bytes],
):
    # Read the bugs from files
    byte_differentials: list[bytes] = []
    differentials = os.listdir(f"{data_folder}/differentials")
    differentials.sort(key=int)
    for diff in differentials:
        differential_file_name = f"{data_folder}/differentials/{diff}"
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
    for fingerprint, byte_differential in zip(fingerprints, byte_differentials):
        fingerprints_to_bytes[fingerprint] = byte_differential
    fingerprints_of_runs[f"{run_name}"] = fingerprints

# Given dictionaries of fingerprints in each run and the bytes those fingerprints correspond to 
def summarize_common_bugs(
    fingerprints_of_runs: dict[str, list[fingerprint_t]], fingerprints_to_bytes: dict[fingerprint_t, bytes]
):
    # Clear current analysis file
    analysis_file_path: str = f"analyses/{sys.argv[1]}.txt"
    open(analysis_file_path, "wb").close() # Clears File
    # Get list of combos from big to small
    combos = list(list(run for run, enabled in zip(sys.argv[2:], enables) if enabled) for enables in itertools.product([True, False], repeat=len(sys.argv[2:])))
    combos.sort(key=len, reverse=True)
    seen_fingerprints: set[fingerprint_t] = set()
    for combo in combos:
        # Save combo name before editing combo
        combo_name: bytes = bytes(",".join(combo), "utf-8")
        # For each combo build list of common bugs
        if not combo: break
        common: set[fingerprint_t] = set(fingerprints_of_runs[combo.pop()])
        for run in combo:
            common = common.intersection(set(fingerprints_of_runs[run]))
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
            comparison_file.write(b"***\n***".join(fingerprints_to_bytes[x] for x in common))
            comparison_file.write(b"***\n")


def build_relative_analysis():
    # Ensure relative comparisons are all present
    for run in set(sys.argv[2:]).difference(os.listdir("runs/")):
        raise FileNotFoundError(f"Couldn't find the data folder for: {run}")

    figure, axis = plt.subplots(2)
    figure.tight_layout(h_pad=2)
    fingerprints_of_runs: dict[str, list[fingerprint_t]] = {}
    fingerprints_to_bytes: dict[fingerprint_t, bytes] = {}

    for run in set(os.listdir("runs")).intersection(sys.argv[2:]):
        data_folder: str = get_data_folder(run)

        plot_data(run, data_folder, axis)

        record_bugs(run, data_folder, fingerprints_of_runs, fingerprints_to_bytes)

    figure.legend(loc="upper left")
    plt.savefig(f"analyses/{sys.argv[1]}.png", format="png")
    plt.close()

    summarize_common_bugs(fingerprints_of_runs, fingerprints_to_bytes)

# Records all bugs from a run into a summary file
def summarize_run(data_folder: str):
    # Get all differential files
    differentials = os.listdir(f"{data_folder}/differentials")
    try:
        differentials.sort(key=int)
    except ValueError as e:
        raise ValueError(f"Issue with {data_folder}/differentials") from e
    for diff_file in differentials:
        # Read the differential bytes from the file
        differential_file_path = f"{data_folder}/differentials/{diff_file}"
        with open(differential_file_path, "rb") as differential_file:
            differential = differential_file.read()
        # Write them into the summary file
        with open(f"{data_folder}/summary.txt", "wb") as summary_file:
            summary_file.write(bytes(diff_file, "utf-8") + b": \n***")
            summary_file.write(differential)
            summary_file.write(b"***\n")



def mass_analysis():
    for run in os.listdir("runs"):
        try:
            data_folder: str = get_data_folder(run)

            figure, axis = plt.subplots(2)
            figure.tight_layout(h_pad=2)

            plot_data(run, data_folder, axis)

            plt.savefig(f"{data_folder}/graphs.png", format="png")
            plt.close()

            summarize_run(data_folder)
        except FileNotFoundError as e:
            print(e)


def main():
    assert os.path.exists("runs")
    assert os.path.exists("analyses")

    if len(sys.argv) > 1:
        build_relative_analysis()
    else:
        mass_analysis()


if __name__ == "__main__":
    main()
