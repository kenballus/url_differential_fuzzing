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


def plot_data(run_name: str, data_folder: str, axis: np.ndarray):
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


def summarize_common_bugs(
    fingerprints_of_runs: dict[str, list[fingerprint_t]], fingerprints_to_bytes: dict[fingerprint_t, bytes]
):
    # Get list of combos from big to small
    combos = list(itertools.product([True, False], repeat=len(sys.argv) - 2))
    combos.sort(key=sum, reverse=True)
    seen_fingerprints: set[fingerprint_t] = set()
    with open(f"analyses/{sys.argv[1]}.txt", "wb") as comparison_file:
        for combo in combos:
            # For each combo build list of common bugs
            common: set[fingerprint_t] = set()
            common_assigned: bool = False
            for enabled, test in zip(combo, sys.argv[2:]):
                if enabled:
                    fingerprints_of_run = fingerprints_of_runs[test]
                    if not common_assigned:
                        common_assigned = True
                        common = set(fingerprints_of_run)
                    else:
                        common = common.intersection(set(fingerprints_of_run))
            common = common - seen_fingerprints
            # Mark bugs as used up
            seen_fingerprints = seen_fingerprints.union(common)

            # Write to the file in a readable byte format
            comparison_file.write(b"-------------------------------------------\n")
            comparison_file.write(
                b",".join(bytes(x, "utf-8") for enabled, x in zip(combo, sys.argv[2:]) if enabled) + b"\n"
            )
            comparison_file.write(b"Total: " + bytes(str(len(common)), "utf-8") + b"\n")
            comparison_file.write(b"-------------------------------------------\n")
            comparison_file.write(b"***")
            comparison_file.write(b"***\n***".join(fingerprints_to_bytes[x] for x in common))
            comparison_file.write(b"***\n")


def build_relative_analysis():
    # Ensure relative comparisons are all present
    for run in sys.argv[2:]:
        if run not in os.listdir("runs/"):
            raise FileNotFoundError(f"Couldn't find the data folder for: {run}")

    figure, axis = plt.subplots(2)
    figure.tight_layout(h_pad=2)
    fingerprints_of_runs: dict[str, list[fingerprint_t]] = {}
    fingerprints_to_bytes: dict[fingerprint_t, bytes] = {}

    for run in os.listdir("runs"):
        if run in sys.argv[2:]:
            data_folder: str = get_data_folder(run)

            plot_data(run, data_folder, axis)

            record_bugs(run, data_folder, fingerprints_of_runs, fingerprints_to_bytes)

    figure.legend(loc="upper left")
    plt.savefig(f"analyses/{sys.argv[1]}.png", format="png")
    plt.close()

    summarize_common_bugs(fingerprints_of_runs, fingerprints_to_bytes)


def summarize_run(data_folder: str):
    with open(f"{data_folder}/summary.txt", "wb") as summary_file:
        differentials = os.listdir(f"{data_folder}/differentials")
        try:
            differentials.sort(key=int)
        except ValueError as e:
            raise ValueError(f"Issue with {data_folder}/differentials") from e
        for diff in differentials:
            summary_file.write(bytes(diff, "utf-8") + b": \n***")
            differential_file_name = f"{data_folder}/differentials/{diff}"
            with open(differential_file_name, "rb") as differential_file:
                summary_file.write(differential_file.read())
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
