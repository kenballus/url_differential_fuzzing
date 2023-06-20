# TODO: Update README

# Benchmarking Instructions

## Set-Up

The benchmarking module has to be setup with appropriate empty folders and files. To do this, run `make` in the benchmarking directory.

## Basic Use

### Benchmarking Queue

In the benchmarking_queue file. Tests can be added as followed.

```$name $commit_hash $timeout [configfile]```

Each test's results will be saved into `runs/$name`

Each test will be run on `commit_hash` with config `configfile`

`configfile` must correspond to the name of a config file in the bench_configs folder

If no config file is specified each test will be run on the same config file as the test before it. If it is the first test it will be run on the current config file.

Each Test will either run out of mutation candidates or will be forcefully ended after `timeout` seconds have elapsed.

Example:

`QueueTest cdab061f174edc301a3fab1c78c5440630d0fbe5 QueueTestConfig.py`

Each test must be followed by a new line character in the file.

A complete benchmarking_queue file should be in the same format as follows:

```
BaseMultipleBytes e7823b0c4cba1d79901f3db50560dcaad8eb90f4 largeByte.py
TestMultipleBytes aa517f562e3138a751a0cf6aa0731134a7fedb1d largeByte.py
TestCombinedMini 7cfc15c1ec954da782daa5a7f69d51439c1262ac combined.py
BaseCombinedMini e4784f7824696825e987c5c2816c0d07850b6b65 combined.py

```

### How to run

Run `./run_benchmarks.sh` with no arguments

Progress will be kept in records.txt and results will be saved to a new directory named after the test in the runs directory

## Analysis

### Test Specific Analysis

Creates a graph and a list of bugs for every completed test in the runs directory.

Run `python analyze.py` with no arguments

Both of these files will be saved in each test's result directory inside the run directory

### Cross Test Analysis

Creates a graph combining all the choosen tests and creates a text file which shows all the bugs that were common between the different tests grouped by the set of tests that they were found in

In the analysis, bugs will be classified by the currently enabled targets in config.py, in most cases you probably want the enabled targets to correspond to the targets the test was originally run with

Run `python analyze.py AnalysisName name1 name2 name3...`

Both of the result files will be saved in the analyses directory

`AnalysisName` is the prefix the resulting analysis files will be saved with 

Each `name` is the name of the test that you want to include in the analysis. Each of these must correspond to a completed test in the runs directory.
