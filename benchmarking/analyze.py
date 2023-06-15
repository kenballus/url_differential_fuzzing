import os
import sys
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import PosixPath
import shutil
import itertools

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from diff_fuzz import trace_batch, fingerprint_t

def main():
    relative: bool = len(sys.argv) > 1

    # Ensure relative comparisons are all present
    for run in sys.argv[2:]:
        if run not in os.listdir("benchmarking/"):
            raise FileNotFoundError(f"Couldn't find the data folder for: {run}")

    if relative:
        figure, axis = plt.subplots(2)
        figure.tight_layout(h_pad=2)
        fingerprints_of_runs: dict[str, list[fingerprint_t]] = {}
        fingerprints_to_bytes: dict[fingerprint_t, bytes] = {}
        

    for run in os.listdir("benchmarking/"):
        data_folder: str = f"benchmarking/{run}"
        if os.path.isdir(data_folder) and (not relative or run in sys.argv):

            print(f"Analyzing: {run}", file=sys.stderr)
            if not os.path.isfile(f"{data_folder}/report.json"):
                raise FileNotFoundError(f"{data_folder} doesn't have a report file!")
            if not os.path.isdir(f"{data_folder}/differentials"):
                raise FileNotFoundError(f"{data_folder} doesn't have a differentials folder!")

            with open(f"{data_folder}/report.json", "r") as report_file:
                report = json.load(report_file)
                differentials = report["Differentials"]
                times: list[float] = []
                generations: list[int] = []
                count: list[int] = []
                running_count: int = 0
                for differential in differentials:
                    running_count += 1
                    generations.append(int(differential["Generation"]))
                    count.append(running_count)
                    times.append(float(differential["Time"]))

                if not relative:
                    figure, axis = plt.subplots(2)
                    figure.tight_layout(h_pad=2)

                # Plot Things
                axis[0].plot(np.array(times), np.array(count), label=run)
                axis[0].set_title("Bugs vs Time")
                axis[1].plot(np.array(generations), np.array(count))
                axis[1].set_title("Bugs vs Generation")

                if not relative:
                    plt.savefig(f"{data_folder}/graphs.png", format="png")
                    plt.close()

            if not relative:
                with open(f"{data_folder}/summary.txt", "wb") as summary_file:
                    differentials = os.listdir(f"{data_folder}/differentials")
                    try:
                        differentials.sort(key=lambda x:int(x))
                    except ValueError:
                        raise ValueError(f"Issue with {data_folder}/differentials")
                    for diff in differentials:
                        summary_file.write(bytes(diff, 'utf-8') + b": \n***")
                        differential_file_name = f"{data_folder}/differentials/{diff}"
                        with open(differential_file_name, "rb") as differential_file:
                            summary_file.write(differential_file.read())
                        summary_file.write(b"***\n")

            if relative:
                byte_differentials: list[bytes] = []
                differentials = os.listdir(f"{data_folder}/differentials")
                differentials.sort(key=lambda x:int(x))
                for diff in differentials:
                    differential_file_name = f"{data_folder}/differentials/{diff}"
                    with open(differential_file_name, "rb") as differential_file:
                        byte_differentials.append(differential_file.read())
                run_dir: PosixPath = PosixPath("/tmp").joinpath(f"analyzer")
                if os.path.exists(run_dir):
                    shutil.rmtree(run_dir)
                os.mkdir(run_dir)
                fingerprints: list[fingerprint_t] = trace_batch(run_dir, byte_differentials)
                shutil.rmtree(run_dir)
                for fingerprint, byte_differential in zip(fingerprints, byte_differentials):
                    fingerprints_to_bytes[fingerprint] = byte_differential
                fingerprints_of_runs[f"{run}"] = fingerprints

    if relative:
        figure.legend(loc="upper left")
        plt.savefig(f"benchmarking/{sys.argv[1]}.png", format="png")
        plt.close()
        combos = list(itertools.product([True, False], repeat=len(sys.argv) - 2))
        combos.sort(key=lambda x:sum(x), reverse=True)
        seen_fingerprints: set[fingerprint_t] = set()
        with open(f'benchmarking/{sys.argv[1]}.txt', 'wb') as comparison_file:
            for combo in combos:
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

                comparison_file.write(b"-------------------------------------------\n")
                comparison_file.write(b','.join(bytes(x, 'utf-8') for enabled, x in zip(combo, sys.argv[2:]) if enabled) + b'\n')
                comparison_file.write(b"Total: " + bytes(str(len(common)), 'utf-8') + b"\n")
                comparison_file.write(b"-------------------------------------------\n")
                comparison_file.write(b"***")
                comparison_file.write(b"***\n***".join(fingerprints_to_bytes[x] for x in common))
                comparison_file.write(b"***\n")
                seen_fingerprints = seen_fingerprints.union(common)
                        
            
if __name__ == "__main__":
    main()