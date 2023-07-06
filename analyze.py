import os
import json
import shutil
import itertools
import uuid
import argparse
from pathlib import PosixPath

import matplotlib.pyplot as plt  # type: ignore
import numpy as np

from diff_fuzz import trace_batch, fingerprint_t

BENCHMARKING_DIR = PosixPath("benchmarking")
RESULTS_DIR = PosixPath("results")
REPORT_DIR = BENCHMARKING_DIR.joinpath("reports")
ANALYSES_DIR = BENCHMARKING_DIR.joinpath("analyses")


def retrieve_data(run_num: int) -> tuple[int, str, str]:
    # Check directories
    if not os.path.isdir(REPORT_DIR):
        raise FileNotFoundError("Report directory doesn't exist!")
    report_folder: PosixPath = REPORT_DIR.joinpath(str(run_num))
    if not os.path.isdir(report_folder):
        raise FileNotFoundError(f"Run #{run_num} doesn't have a report folder!")

    # Retrieve name
    name_file_path: PosixPath = report_folder.joinpath("name.txt")
    if not os.path.isfile(name_file_path):
        raise FileNotFoundError(f"Run #{run_num} doesn't have a name file!")
    with open(name_file_path, "r", encoding="utf-8") as name_file:
        run_name = name_file.read()

    # Retrieve UUID
    report_file_path: PosixPath = report_folder.joinpath("report.json")
    if not os.path.isfile(report_file_path):
        raise FileNotFoundError(f"{run_name} doesn't have a report file!")
    with open(report_file_path, "r", encoding="utf-8") as report_file:
        report = json.load(report_file)
        run_uuid = report["uuid"]

    # Check for results folder
    if not os.path.isdir(RESULTS_DIR.joinpath(run_uuid)):
        raise FileNotFoundError(f"{run_name} doesn't have a differentials folder!")

    return (run_num, run_name, run_uuid)


# Plot a run onto a given axis
def plot_bugs(run_name: str, report_file_path: PosixPath, axis: np.ndarray) -> None:
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
    fingerprints: list[fingerprint_t] = trace_batch(run_dir, byte_differentials)
    shutil.rmtree(run_dir)

    # Record
    fingerprints_bytes = {}
    for fingerprint, byte_differential in zip(fingerprints, byte_differentials):
        fingerprints_bytes[fingerprint] = byte_differential
    return fingerprints_bytes


# Given dictionaries of fingerprints in each run and the bytes those fingerprints correspond to
def build_overlap_reports(
    runs_to_analyze: set[tuple[int, str, str]],
    summary_file_path: PosixPath,
    machine_file_path: PosixPath,
    analysis_name: str,
) -> None:
    print("Building Overlap Reports...")
    run_differentials: dict[str, dict[fingerprint_t, bytes]] = {}
    for _, run_name, run_uuid in runs_to_analyze:
        run_differentials[run_name] = get_fingerprint_differentials(RESULTS_DIR.joinpath(run_uuid))
    # Setup analysis file and machine file
    with open(summary_file_path, "wb") as analysis_file:
        analysis_file.write(f"Analysis: {analysis_name}\n".encode("utf-8"))
    with open(machine_file_path, "w", encoding="utf-8") as machine_file:
        machine_file.write(f"{','.join(run_name for _, run_name, _ in runs_to_analyze)},count\n")
    # Get list of combos from big to small
    enables_list = list(itertools.product([True, False], repeat=len(runs_to_analyze)))
    enables_list.sort(key=sum, reverse=True)
    seen_fingerprints: set[fingerprint_t] = set()
    for enables in enables_list:
        # Create combo from enabled runs
        combo = list(run_name for (_, run_name, _), enabled in zip(runs_to_analyze, enables) if enabled)
        # Save combo name before editing combo
        combo_name: bytes = bytes(",".join(combo), "utf-8")
        # For each combo build list of common bugs
        if not combo:
            break
        first_run: dict[fingerprint_t, bytes] = run_differentials[combo.pop()]
        common: set[fingerprint_t] = set(first_run.keys())
        for run_name in combo:
            common = common.intersection(run_differentials[run_name].keys())
        # Write to the machine readable file
        with open(machine_file_path, "a", encoding="utf-8") as machine_file:
            machine_file.write(f"{','.join(str(enable) for enable in enables)},{len(common)}\n")
        # Take away already used bugs and mark bugs as used up
        unused_common = common - seen_fingerprints
        seen_fingerprints = seen_fingerprints.union(unused_common)
        # Write to the summary file in a readable byte format
        with open(summary_file_path, "ab") as comparison_file:
            comparison_file.write(b"-------------------------------------------\n")
            comparison_file.write(combo_name + b"\n")
            comparison_file.write(b"Total: " + bytes(str(len(unused_common)), "utf-8") + b"\n")
            comparison_file.write(b"-------------------------------------------\n")
            comparison_file.write(b"***")
            comparison_file.write(b"***\n***".join(first_run[x] for x in unused_common))
            comparison_file.write(b"***\n")


def build_edge_graphs(
    analysis_name: str, runs_to_analyze: list[tuple[int, str, str]], analysis_folder: PosixPath
) -> None:
    print("Building Edge Graphs...")
    # Gather The Data
    edge_data: dict[str, tuple[tuple[list[int], list[float], list[int]], ...]] = {}

    for i, (run_num, _, _) in enumerate(runs_to_analyze):
        report = json.loads(
            open(REPORT_DIR.joinpath(str(run_num)).joinpath("report.json"), "r", encoding="utf-8").read()
        )
        coverage = report["coverage"]
        for target_name in coverage.keys():
            if target_name not in edge_data:
                edge_data[target_name] = tuple(([], [], []) for _ in runs_to_analyze)
            for data_point in coverage[target_name]:
                edge_data[target_name][i][0].append(int(data_point["edges"]))
                edge_data[target_name][i][1].append(float(data_point["time"]))
                edge_data[target_name][i][2].append(int(data_point["generation"]))

    # Build The Graphs
    for target_name, runs in edge_data.items():
        figure, axis = plt.subplots(2, 1, constrained_layout=True)
        figure.suptitle(f"{analysis_name} - {target_name}", fontsize=16)
        axis[0].set_xlabel("Time (s)")
        axis[0].set_ylabel("Edges")
        axis[1].set_xlabel("Generations")
        axis[1].set_ylabel("Edges")
        for i, run in enumerate(runs):
            axis[0].plot(np.array(run[1]), np.array(run[0]), label=runs_to_analyze[i][0])
            axis[1].plot(np.array(run[2]), np.array(run[0]))
        figure.legend(loc="upper left")
        plt.savefig(analysis_folder.joinpath(f"edges_{target_name}").with_suffix(".png"), format="png")
        plt.close()


def build_bug_graph(
    analysis_name: str, runs_to_analyze: set[tuple[int, str, str]], analysis_folder: PosixPath
) -> None:
    print("Building Bug Graph...")
    figure, axis = plt.subplots(2, 1, constrained_layout=True)
    figure.suptitle(analysis_name, fontsize=16)

    for run_num, run_name, _ in runs_to_analyze:
        plot_bugs(run_name, REPORT_DIR.joinpath(str(run_num)).joinpath("report.json"), axis)

    figure.legend(loc="upper left")
    plt.savefig(analysis_folder.joinpath("bug_graph").with_suffix(".png"), format="png")
    plt.close()


def main() -> None:
    assert os.path.exists(RESULTS_DIR)
    assert os.path.exists(ANALYSES_DIR)
    assert os.path.exists(REPORT_DIR)

    # Retrieve Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=str, default="Analysis", help="The Name of the Analysis to Create")
    parser.add_argument("-b", help="Enable Creation of Bug Graph", action="store_true")
    parser.add_argument("-v", help="Enable Creation of Overlap Reports", action="store_true")
    parser.add_argument("-e", help="Enable Creation of Edge graphs", action="store_true")
    args = parser.parse_args()

    # ensure at least one option is enabled
    assert any((args.b, args.v, args.e))

    runs_to_analyze: set[tuple[int, str, str]] = set()
    for report_folder in os.listdir(REPORT_DIR):
        runs_to_analyze.add(retrieve_data(int(report_folder)))

    analysis_uuid: str = str(uuid.uuid4())
    analysis_folder: PosixPath = ANALYSES_DIR.joinpath(analysis_uuid)
    os.mkdir(analysis_folder)

    if args.b:
        build_bug_graph(args.n, runs_to_analyze, analysis_folder)
    if args.e:
        build_edge_graphs(args.n, list(runs_to_analyze), analysis_folder)
    if args.v:
        build_overlap_reports(
            runs_to_analyze,
            analysis_folder.joinpath("overlap_summary").with_suffix(".txt"),
            analysis_folder.joinpath("overlap_machine").with_suffix(".csv"),
            args.n,
        )

    print(f"Analysis Path: {analysis_folder}")


if __name__ == "__main__":
    main()
