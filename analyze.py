import os
import json
import shutil
import itertools
import uuid
import argparse
import subprocess
from pathlib import PosixPath
from dataclasses import dataclass

import matplotlib.pyplot as plt  # type: ignore
import numpy as np

from diff_fuzz import trace_batch, fingerprint_t

BENCHMARKING_DIR: PosixPath = PosixPath("benchmarking")
RESULTS_DIR: PosixPath = PosixPath("results")
REPORTS_DIR: PosixPath = PosixPath("reports")
ANALYSES_DIR: PosixPath = BENCHMARKING_DIR.joinpath("analyses")

CONFIG_FILE_PATH: PosixPath = PosixPath("config.py")
CONFIG_COPY_PATH: PosixPath = BENCHMARKING_DIR.joinpath("config_copy.py")
CONFIGS_DIR: PosixPath = BENCHMARKING_DIR.joinpath("bench_configs")


def assert_data(run_name: str, run_uuid: str) -> None:
    # Check directories
    if not os.path.isfile(REPORTS_DIR.joinpath(run_uuid).with_suffix(".json")):
        raise FileNotFoundError(f"{run_name} doesn't have a report file!")

    # Check for results folder
    if not os.path.isdir(RESULTS_DIR.joinpath(run_uuid)):
        raise FileNotFoundError(f"{run_name} doesn't have a differentials folder!")


@dataclass
class edge_datapoint:
    edge_count: int
    time: float
    generation: int

    def assert_types(self) -> None:
        assert isinstance(self.edge_count, int)
        assert isinstance(self.time, float)
        assert isinstance(self.generation, int)


@dataclass
class bug_datapoint:
    bug_count: int
    time: float
    generation: int

    def assert_types(self) -> None:
        assert isinstance(self.bug_count, int)
        assert isinstance(self.time, float)
        assert isinstance(self.generation, int)


def parse_reports(
    runs_to_analyze: list[tuple[str, str]]
) -> tuple[dict[str, list[bug_datapoint]], dict[str, tuple[list[edge_datapoint], ...]]]:
    all_bug_data: dict[str, list[bug_datapoint]] = {}
    all_edge_data: dict[str, tuple[list[edge_datapoint], ...]] = {}
    for i, (_, run_uuid) in enumerate(runs_to_analyze):
        with open(REPORTS_DIR.joinpath(run_uuid).with_suffix(".json"), "rb") as report_file:
            report_json: dict = json.load(report_file)
            assert isinstance(report_json, dict)

        # Parse the JSON for bug data
        differentials_json: list[dict] = report_json["differentials"]
        assert isinstance(differentials_json, list)
        differentials: list[bug_datapoint] = []
        running_count: int = 0
        for differential_json in differentials_json:
            assert isinstance(differential_json, dict)
            running_count += 1
            bug_data: bug_datapoint = bug_datapoint(
                running_count, differential_json["time"], differential_json["generation"]
            )
            bug_data.assert_types()
            differentials.append(bug_data)
        all_bug_data[run_uuid] = differentials

        # Parse the JSON for edge data
        coverage_json: dict[str, list[dict]] = report_json["coverage"]
        assert isinstance(coverage_json, dict)
        for target_name in coverage_json.keys():
            assert isinstance(target_name, str)
            if target_name not in all_edge_data:
                all_edge_data[target_name] = tuple([] for _ in runs_to_analyze)
            for data_point_json in coverage_json[target_name]:
                assert isinstance(data_point_json, dict)
                edge_data: edge_datapoint = edge_datapoint(
                    data_point_json["edges"], data_point_json["time"], data_point_json["generation"]
                )
                edge_data.assert_types()
                all_edge_data[target_name][i].append(edge_data)
    return all_bug_data, all_edge_data


# ????
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


def build_overlap_reports(
    runs_to_analyze: list[tuple[str, str]],
    summary_file_path: PosixPath,
    machine_file_path: PosixPath,
    analysis_name: str,
) -> None:
    print("Building Overlap Reports...")
    run_differentials: dict[str, dict[fingerprint_t, bytes]] = {}
    for run_name, run_uuid in runs_to_analyze:
        run_differentials[run_name] = get_fingerprint_differentials(RESULTS_DIR.joinpath(run_uuid))
    # Setup analysis file and machine file
    with open(summary_file_path, "wb") as analysis_file:
        analysis_file.write(f"Analysis: {analysis_name}\n".encode("utf-8"))
    with open(machine_file_path, "w", encoding="utf-8") as machine_file:
        machine_file.write(f"{','.join(run_name for run_name, _ in runs_to_analyze)},count\n")
    # Get list of combos from big to small
    enables_list = list(itertools.product([True, False], repeat=len(runs_to_analyze)))
    enables_list.sort(key=sum, reverse=True)
    seen_fingerprints: set[fingerprint_t] = set()
    for enables in enables_list:
        # Create combo from enabled runs
        combo = list(run_name for (run_name, _), enabled in zip(runs_to_analyze, enables) if enabled)
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
    analysis_name: str,
    runs_to_analyze: list[tuple[str, str]],
    analysis_dir: PosixPath,
    edge_data: dict[str, tuple[list[edge_datapoint], ...]],
) -> None:
    print("Building Edge Graphs...")

    # Build The Graphs
    for target_name, runs in edge_data.items():
        figure, axis = plt.subplots(2, 1, constrained_layout=True)
        figure.suptitle(f"{analysis_name} - {target_name}", fontsize=16)
        axis[0].set_xlabel("Time (s)")
        axis[0].set_ylabel("Edges")
        axis[1].set_xlabel("Generations")
        axis[1].set_ylabel("Edges")
        for i, run in enumerate(runs):
            axis[0].plot(
                np.array([point.time for point in run]),
                np.array([point.edge_count for point in run]),
                label=runs_to_analyze[i][0],
            )
            axis[1].plot(
                np.array([point.generation for point in run]), np.array([point.edge_count for point in run])
            )
        figure.legend(loc="upper left")
        plt.savefig(analysis_dir.joinpath(f"edges_{target_name}").with_suffix(".png"), format="png")
        plt.close()


# Plot a run onto a given axis
def plot_bugs(run_name: str, differentials: list[bug_datapoint], axis: np.ndarray) -> None:
    # Plot Things
    axis[0].plot(
        np.array([differential.time for differential in differentials]),
        np.array([differential.bug_count for differential in differentials]),
        label=run_name,
    )
    axis[0].set_xlabel("Time (s)")
    axis[0].set_ylabel("Bugs")
    axis[1].plot(
        np.array([differential.generation for differential in differentials]),
        np.array([differential.bug_count for differential in differentials]),
    )
    axis[1].set_xlabel("Generations")
    axis[1].set_ylabel("Bugs")


def build_bug_graph(
    analysis_name: str,
    runs_to_analyze: list[tuple[str, str]],
    analysis_dir: PosixPath,
    bug_data: dict[str, list[bug_datapoint]],
) -> None:
    print("Building Bug Graph...")
    figure, axis = plt.subplots(2, 1, constrained_layout=True)
    figure.suptitle(analysis_name, fontsize=16)

    for run_name, run_uuid in runs_to_analyze:
        plot_bugs(run_name, bug_data[run_uuid], axis)

    figure.legend(loc="upper left")
    plt.savefig(analysis_dir.joinpath("bug_graph").with_suffix(".png"), format="png")
    plt.close()

@dataclass
class QueuedRun:
    name: str
    commit: str
    timeout: int
    config: str | None

def main() -> None:
    assert RESULTS_DIR.is_dir()
    assert ANALYSES_DIR.is_dir()
    assert REPORTS_DIR.is_dir()
    assert CONFIGS_DIR.is_dir()

    # Retrieve arguments
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("queue_file_path", help="The path to the queue file to take runs from for the analysis")
    parser.add_argument("--name", help="TODO: Remove", required=True)
    parser.add_argument("--bug-count", help="Enable creation of bug count plot", action="store_true")
    parser.add_argument("--bug-overlap", help="Enable creation of bug overlap reports", action="store_true")
    parser.add_argument("--edge-count", help="Enable creation of edge count plot", action="store_true")
    args: argparse.Namespace = parser.parse_args()

    # ensure at least one option is enabled
    if not any((args.bug_count, args.edge_count, args.bug_overlap)):
        raise ValueError("At least one of --bug-count, --bug-overlap, --edge-count must be passed.")

    # Check that queue file exists
    queue_file_path = PosixPath(args.queue_file_path)
    assert os.path.isfile(queue_file_path)

    # Copy the config
    assert os.path.isfile(CONFIG_FILE_PATH)
    shutil.copyfile(CONFIG_FILE_PATH, CONFIG_COPY_PATH)

    # Save original branch
    original_branch: bytes = subprocess.run(["git","branch","--show-current"], capture_output=True, check=True).stdout.strip()

    queued_runs: list[QueuedRun] = []
    # Read queue file and check validity
    with open(queue_file_path, "r") as queue_file:
        for line in queue_file.readlines():
            split_line: list[str] = line.strip().split(",")
            if len(split_line) < 3:
                raise ValueError(f"Queue line {line.strip()} has too few arguments.")
            if len(split_line) > 4:
                raise ValueError(f"Queue line {line.strip()} has too many arguments.")
            config: str | None = None
            if len(split_line) == 4:
                config = split_line[3]
                if not CONFIGS_DIR.joinpath(config).is_file():
                    raise ValueError(f"{config} is not a valid config in the configs directory.")
            try:
                timeout: int = int(split_line[2])
            except ValueError as e:
                raise ValueError(f"Timeout {split_line[2]} must be an integer") from e
            queued_runs.append(QueuedRun(split_line[0], split_line[1], timeout, config))

    runs_to_analyze: list[tuple[str,str]] = []

    # Execute queued runs
    for queued_run in queued_runs:
        subprocess.run(["git","checkout",queued_run.commit], check=True)
        if queued_run.config is None:
            shutil.copyfile(CONFIG_COPY_PATH, CONFIG_FILE_PATH)
        else:
            shutil.copyfile(CONFIGS_DIR.joinpath(queued_run.config), CONFIG_FILE_PATH)
        runs_to_analyze.append(queued_run.name, str(subprocess.run(["timeout", "--foreground", "--signal=2" , str(queued_run.timeout), "python", "diff_fuzz.py"], capture_output=True, check=True).stdout, encoding='ascii').strip())

    # Cleanup
    subprocess.run(["git","switch",original_branch], capture_output=True, check=True)
    shutil.copyfile(CONFIG_COPY_PATH, CONFIG_FILE_PATH)
    os.remove(CONFIG_COPY_PATH)

    for x in runs_to_analyze:
        print(x)

    return

    # Running of tests should be done in python
    # Should return uuids, these are temp
    runs_to_analyze: list[tuple[str, str]] = [
        ("Name1", "5c483e92-0a72-422e-8afd-55bb8796bccc"),
        ("Name2", "9b2760f8-e0dc-4a97-98a5-aa123f0dbc07"),
        ("Name3", "3be9388c-7829-4737-a6fe-be1b997670f7"),
    ]

    for run_name, run_uuid in runs_to_analyze:
        assert_data(run_name, run_uuid)
    try:
        bug_data, edge_data = parse_reports(runs_to_analyze)
    except AssertionError as e:
        raise ValueError("One of the report JSON files cannot be parsed.") from e

    analysis_uuid: str = str(uuid.uuid4())
    analysis_dir: PosixPath = ANALYSES_DIR.joinpath(analysis_uuid)
    os.mkdir(analysis_dir)

    if args.bug_count:
        build_bug_graph(args.name, runs_to_analyze, analysis_dir, bug_data)
    if args.edge_count:
        build_edge_graphs(args.name, runs_to_analyze, analysis_dir, edge_data)
    if args.bug_overlap:
        build_overlap_reports(
            runs_to_analyze,
            analysis_dir.joinpath("overlap_summary").with_suffix(".txt"),
            analysis_dir.joinpath("overlap_machine").with_suffix(".csv"),
            args.name,
        )

    print(f"Analysis done! See {analysis_dir.resolve()} for results")


if __name__ == "__main__":
    main()
