import os
import sys
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import PosixPath
from tqdm import tqdm
import shutil
import itertools

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from config import TargetConfig, TARGET_CONFIGS, compare_parse_trees
from diff_fuzz import run_targets

def main():

    run_of_interest_path = sys.argv[1]

    if run_of_interest_path not in os.listdir("benchmarking/"):
        raise FileNotFoundError(f"Couldn't find the data folder for: {run_of_interest_path}")
    
    run_of_interest_path = os.path.join("benchmarking/", run_of_interest_path)

    differential_folder = os.path.join(run_of_interest_path, "differentials")

    diff_count: dict[tuple[int, int], int] = {}
    for idx_pair in itertools.combinations(range(len(TARGET_CONFIGS)), 2):
        diff_count[idx_pair] = 0

    for differential_file_path in tqdm(os.listdir(differential_folder)):
        with open(os.path.join(differential_folder, differential_file_path), "rb") as differential_file:
            statuses, parse_trees = run_targets(differential_file.read())
            for idx_pair in diff_count.keys():
                if statuses[idx_pair[0]] != statuses[idx_pair[1]] or not all(compare_parse_trees(parse_trees[idx_pair[0]], parse_trees[idx_pair[1]])):
                    diff_count[idx_pair] += 1

    for idx_pair, tc_pair in zip(diff_count.keys(), itertools.combinations((tc.name for tc in TARGET_CONFIGS), 2)):
        print(f"{tc_pair} -----> {diff_count[idx_pair]}")


if __name__ == "__main__":
    main()