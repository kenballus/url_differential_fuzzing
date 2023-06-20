# Benchmarking Instructions

## Set-Up

The benchmarking module has to be setup with appropriate empty folders. To do this, run `make` in the benchmarking directory.

## Basic Use

### Benchmarking Queues

Before tests can be run the user must first create a benchmarking queue file.

Tests can be added to a queue as follows:

```$name,$commit_hash,$timeout,[configfile]```

Each test will be run on `commit_hash` with config `configfile`.

`configfile` must correspond to the name of a config file in the bench_configs folder.

If no config file is specified then the test will be run on the current config file.

Each test will be forcefully ended after `timeout` seconds have elapsed or will run out of mutation candidates.

Complete Benchmarking Queue File Example:

```
Test A,043f804572d88cfd7be1dc7247bef28d875b0d60,30,rfc_url.py
Test B,043f804572d88cfd7be1dc7247bef28d875b0d60,30
Test C,b7aa710177b48a680e97d9851b34bcab366626cf,30,rfc_url.py
```

### How to run

Run `./run_benchmarks.sh analysis_name < benchmarking_queue`.

`analysis_name` will be the label for the final analysis graph and text output.

`benchmarking_queue` should be a completed benchmarking queue file that contains all the tests you want to compare.

It is suggested you keep benchmarking queue files in the queues directory but they can be kept anywhere.

### Output

Progress will be kept in records.txt and analysis results will be saved in the analyses directory under a uuid.

The uuid for the analysis will be printed to stdout after the program runs.

The uuid folder will contain two items, a .png and a .txt file.

The .png file is a graph which compares all the queued tests. It has a figure for bugs over time and a figure for bugs over generations.

The .txt file groups every found bug by the largest set of queued tests that commonly found it.

Bugs are classified according to the current config
