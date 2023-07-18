import os
import json
import shutil
import itertools
import uuid
import argparse
import subprocess
import sys
from pathlib import PosixPath
from dataclasses import dataclass

import matplotlib.pyplot as plt  # type: ignore
import numpy as np

from diff_fuzz import trace_batch, fingerprint_t, json_t, json_obj_t

BENCHMARKING_DIR: PosixPath = PosixPath("benchmarking")
RESULTS_DIR: PosixPath = PosixPath("results")
REPORTS_DIR: PosixPath = PosixPath("reports")
ANALYSES_DIR: PosixPath = BENCHMARKING_DIR.joinpath("analyses")

CONFIG_FILE_PATH: PosixPath = PosixPath("config.py")
CONFIG_COPY_PATH: PosixPath = BENCHMARKING_DIR.joinpath("config_copy.py")
CONFIGS_DIR: PosixPath = BENCHMARKING_DIR.joinpath("bench_configs")


# Check that the files exported by a given run of the fuzzer actually exist
def check_fuzz_output(run_name: str, run_uuid: str) -> None:
    # Check for report file
    if not os.path.isfile(REPORTS_DIR.joinpath(run_uuid).with_suffix(".json")):
        raise FileNotFoundError(f"{run_name} doesn't have a report file!")

    # Check for results folder
    if not os.path.isdir(RESULTS_DIR.joinpath(run_uuid)):
        raise FileNotFoundError(f"{run_name} doesn't have a differentials folder!")


# Data class for holding information about how many cumulative unique edges of each parser were found in each generation and at what time.
# Stored in JSON in the coverage list which has a list for each parser, these lists consist of JSON objects for each generation which record generation, time, and
# number of unique edges uncovered in that parser up to that generation.
@dataclass
class EdgeDatapoint:
    edge_count: int
    time: float
    generation: int


# Data class for holding information about how many cumulative unique bugs were found by the run at times when new bugs were found. Records the
# cumulative number of bugs found up to that point, the time at which the latest included bug was found, and the generation at which the latest included bug was found.
# Stored in JSON in the differentials list which has a JSON object for every bug found during the run sorted by time found in ascending order. Each JSON object has an
# example of the bug base64 encoded, the path to a file where an example of the bug is stored, the time at which the bug was found, and the generation when the bug was found.
@dataclass
class BugDatapoint:
    bug_count: int
    time: float
    generation: int


def parse_reports(
    uuids_to_names: dict[str, str]
) -> tuple[dict[str, list[BugDatapoint]], dict[str, dict[str, list[EdgeDatapoint]]]]:
    all_bug_data: dict[str, list[BugDatapoint]] = {}
    all_edge_data: dict[str, dict[str, list[EdgeDatapoint]]] = {}
    for run_uuid in uuids_to_names:
        with open(REPORTS_DIR.joinpath(run_uuid).with_suffix(".json"), "rb") as report_file:
            report_json: json_obj_t = json.load(report_file)
            assert isinstance(report_json, dict)

        # Parse the JSON for bug datas
        differentials_json: json_t = report_json["differentials"]
        assert isinstance(differentials_json, list)
        differentials: list[BugDatapoint] = []
        running_count: int = 0
        for differential_json in differentials_json:
            assert isinstance(differential_json, dict)
            running_count += 1
            assert isinstance(differential_json["time"], float)
            assert isinstance(differential_json["generation"], int)
            bug_data: BugDatapoint = BugDatapoint(
                running_count, differential_json["time"], differential_json["generation"]
            )
            differentials.append(bug_data)
        all_bug_data[run_uuid] = differentials

        # Parse the JSON for edge data
        coverage_json: json_t = report_json["coverage"]
        assert isinstance(coverage_json, dict)
        for target_name in coverage_json.keys():
            assert isinstance(target_name, str)
            if target_name not in all_edge_data:
                all_edge_data[target_name] = {run_uuid: [] for run_uuid in uuids_to_names}
            coverage_list: json_t = coverage_json[target_name]
            assert isinstance(coverage_list, list)
            for data_point_json in coverage_list:
                assert isinstance(data_point_json, dict)
                assert isinstance(data_point_json["edges"], int)
                assert isinstance(data_point_json["time"], float)
                assert isinstance(data_point_json["generation"], int)
                edge_data: EdgeDatapoint = EdgeDatapoint(
                    data_point_json["edges"], data_point_json["time"], data_point_json["generation"]
                )
                all_edge_data[target_name][run_uuid].append(edge_data)
    return all_bug_data, all_edge_data


# Reads byte differentials from the given differentials directory and gives them back in a list
def read_byte_differentials(
    differentials_folder: PosixPath,
) -> list[bytes]:
    # Read the bugs from files
    byte_differentials: list[bytes] = []
    differentials = os.listdir(differentials_folder)
    for diff in differentials:
        differential_file_name = differentials_folder.joinpath(diff)
        with open(differential_file_name, "rb") as differential_file:
            byte_differentials.append(differential_file.read())
    return byte_differentials


# Takes a list of byte differentials and returns a dictionary of all the trace fingerprints these byte differentials result in.
# The dictionary maps each found fingerprint to a byte differential example.
def trace_byte_differentials(byte_differentials: list[bytes]) -> dict[fingerprint_t, bytes]:
    # Trace the bugs
    run_dir: PosixPath = PosixPath("/tmp").joinpath("analyzer")
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    os.mkdir(run_dir)
    fingerprints: list[fingerprint_t] = trace_batch(run_dir, byte_differentials)
    shutil.rmtree(run_dir)

    # Record
    fingerprints_to_bytes = {}
    for fingerprint, byte_differential in zip(fingerprints, byte_differentials):
        fingerprints_to_bytes[fingerprint] = byte_differential
    return fingerprints_to_bytes


def build_overlap_report(
    uuids_to_names: dict[str, str],
    machine_file_path: PosixPath,
) -> None:
    run_differentials: dict[str, dict[fingerprint_t, bytes]] = {}
    for run_uuid in uuids_to_names:
        byte_differentials: list[bytes] = read_byte_differentials(RESULTS_DIR.joinpath(run_uuid))
        run_differentials[run_uuid] = trace_byte_differentials(byte_differentials)
    uuid_list: list[str] = list(uuids_to_names)

    # Get list of combos from big to small
    combos_list: list[list[str]] = list(
        list(run_uuid for run_uuid, enabled in zip(uuid_list, enables) if enabled)
        for enables in list(itertools.product([True, False], repeat=len(uuid_list)))
    )
    combos_list.sort(key=len, reverse=True)
    combo_name_to_traces: dict[str, set[fingerprint_t]] = {}
    for combo in combos_list:
        # Save combo name before editing combo
        combo_name: str = "/".join(uuids_to_names[run_uuid] for run_uuid in combo)
        # For each combo build list of common bugs
        if not combo:
            break
        common_traces: set[fingerprint_t] = set(run_differentials[combo.pop()].keys())
        for run_uuid in combo:
            common_traces = common_traces.intersection(run_differentials[run_uuid].keys())
        combo_name_to_traces[combo_name] = common_traces

    # Write to the machine readable file
    with open(machine_file_path, "wb") as machine_file:
        machine_file.write("Included runs,Common bug count\n".encode("latin-1"))
        machine_file.write(
            "\n".join(
                f"{combo_name},{len(common_traces)}"
                for combo_name, common_traces in combo_name_to_traces.items()
            ).encode("latin-1")
        )

    # Choose examples for every trace
    trace_examples: dict[fingerprint_t, bytes] = {}
    for traces_to_bytes in run_differentials.values():
        for trace in traces_to_bytes:
            trace_examples[trace] = traces_to_bytes[trace]

    # Write to the stderr file in a readable format
    for combo_name, common_traces in combo_name_to_traces.items():
        print("-------------------------------------------", file=sys.stderr)
        print(combo_name, file=sys.stderr)
        print("Total: " + str(len(common_traces)), file=sys.stderr)
        print("-------------------------------------------", file=sys.stderr)
        # Find an example for each trace common between the runs
        common_examples: list[str] = list(str(trace_examples[trace])[2:-1] for trace in common_traces)
        # Sort examples and print them
        common_examples.sort()
        for example in common_examples:
            print(example, file=sys.stderr)


def build_edge_graphs(
    analysis_name: str,
    uuids_to_names: dict[str, str],
    analysis_dir: PosixPath,
    edge_data: dict[str, dict[str, list[EdgeDatapoint]]],
) -> None:
    # Build the graphs
    for target_name, runs in edge_data.items():
        figure, axis = plt.subplots(2, 1, constrained_layout=True)
        figure.suptitle(f"{analysis_name} - {target_name}", fontsize=16)
        axis[0].set_xlabel("Time (s)")
        axis[0].set_ylabel("Edges")
        axis[1].set_xlabel("Generations")
        axis[1].set_ylabel("Edges")
        for run_uuid in runs:
            axis[0].plot(
                np.array([point.time for point in runs[run_uuid]]),
                np.array([point.edge_count for point in runs[run_uuid]]),
                label=uuids_to_names[run_uuid],
            )
            axis[1].plot(
                np.array([point.generation for point in runs[run_uuid]]),
                np.array([point.edge_count for point in runs[run_uuid]]),
            )
        figure.legend(loc="upper left")
        plt.savefig(analysis_dir.joinpath(f"edges_{target_name}").with_suffix(".png"), format="png")
        plt.close()


# Plot a run onto a given axis
def plot_bugs(run_name: str, differentials: list[BugDatapoint], axis: np.ndarray) -> None:
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
    uuids_to_names: dict[str, str],
    analysis_dir: PosixPath,
    bug_data: dict[str, list[BugDatapoint]],
) -> None:
    figure, axis = plt.subplots(2, 1, constrained_layout=True)
    figure.suptitle(analysis_name, fontsize=16)

    for run_uuid, run_name in uuids_to_names.items():
        plot_bugs(run_name, bug_data[run_uuid], axis)

    figure.legend(loc="upper left")
    plt.savefig(analysis_dir.joinpath("bug_graph").with_suffix(".png"), format="png")
    plt.close()


# Dataclass for holding information about runs in the queue. Contains a user-defined name, a commit hash,
# a timeout in seconds, and potentially a config for the run
@dataclass
class QueuedRun:
    name: str
    commit: str
    timeout: int
    config: str | None


def retrieve_queued_runs(queue_file_path: PosixPath) -> list[QueuedRun]:
    queued_runs: list[QueuedRun] = []
    # Read queue file and check validity
    with open(queue_file_path, "r", encoding="ascii") as queue_file:
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
    return queued_runs


def execute_runs(queued_runs: list[QueuedRun]) -> dict[str, str]:
    # Copy the config
    assert os.path.isfile(CONFIG_FILE_PATH)
    shutil.copyfile(CONFIG_FILE_PATH, CONFIG_COPY_PATH)

    # Save original branch
    original_branch: bytes = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, check=True
    ).stdout.strip()

    uuids_to_names: dict[str, str] = {}

    # Execute queued runs
    for queued_run in queued_runs:
        subprocess.run(["git", "checkout", queued_run.commit], check=True)
        if queued_run.config is None:
            shutil.copyfile(CONFIG_COPY_PATH, CONFIG_FILE_PATH)
        else:
            shutil.copyfile(CONFIGS_DIR.joinpath(queued_run.config), CONFIG_FILE_PATH)
        uuids_to_names[
            str(
                subprocess.run(
                    [
                        "timeout",
                        "--foreground",
                        "--signal=2",
                        "--preserve-status",
                        str(queued_run.timeout),
                        "python",
                        "diff_fuzz.py",
                    ],
                    capture_output=True,
                    check=True,
                ).stdout,
                encoding="ascii",
            ).strip()
        ] = queued_run.name

    # Cleanup
    subprocess.run(["git", "switch", original_branch], capture_output=True, check=True)
    shutil.copyfile(CONFIG_COPY_PATH, CONFIG_FILE_PATH)
    os.remove(CONFIG_COPY_PATH)

    return uuids_to_names


def main() -> None:
    assert RESULTS_DIR.is_dir()
    assert ANALYSES_DIR.is_dir()
    assert REPORTS_DIR.is_dir()
    assert CONFIGS_DIR.is_dir()

    # Retrieve arguments
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("name", help="The name of the analysis to put on the graphs")
    parser.add_argument(
        "queue_file_path", help="The path to the queue file to take runs from for the analysis"
    )
    parser.add_argument("--bug-count", help="Enable creation of bug count plot", action="store_true")
    parser.add_argument("--bug-overlap", help="Enable creation of bug overlap reports", action="store_true")
    parser.add_argument("--edge-count", help="Enable creation of edge count plot", action="store_true")
    args: argparse.Namespace = parser.parse_args()

    # Ensure at least one option is enabled
    if not any((args.bug_count, args.edge_count, args.bug_overlap)):
        raise ValueError("At least one of --bug-count, --bug-overlap, --edge-count must be passed.")

    # Check that queue file exists and get queued runs
    queue_file_path = PosixPath(args.queue_file_path)
    assert os.path.isfile(queue_file_path)
    queued_runs: list[QueuedRun] = retrieve_queued_runs(queue_file_path)

    # Run!
    uuids_to_names: dict[str, str] = execute_runs(queued_runs)

    # Parse and assert data
    for run_uuid, run_name in uuids_to_names.items():
        check_fuzz_output(run_name, run_uuid)
    try:
        bug_data, edge_data = parse_reports(uuids_to_names)
    except AssertionError as e:
        raise ValueError("One of the report JSON files cannot be parsed.") from e

    # Generate analysis uuid
    analysis_uuid: str = str(uuid.uuid4())
    analysis_dir: PosixPath = ANALYSES_DIR.joinpath(analysis_uuid)
    os.mkdir(analysis_dir)

    if args.bug_count:
        build_bug_graph(args.name, uuids_to_names, analysis_dir, bug_data)
    if args.edge_count:
        build_edge_graphs(args.name, uuids_to_names, analysis_dir, edge_data)
    if args.bug_overlap:
        build_overlap_report(
            uuids_to_names,
            analysis_dir.joinpath("overlap_machine").with_suffix(".csv"),
        )

    print(f"Analysis done! See {analysis_dir.resolve()} for results")


if __name__ == "__main__":
    main()
