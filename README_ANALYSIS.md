## Benchmarking Instructions

## Set-Up

The benchmarking module has to be setup with appropriate empty folders. To do this, run `make` in the benchmarking directory.

## Benchmarking Queues

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

## How to run

Run `./run_benchmarks.sh -n name_of_analysis [-b] [-e] [-v] < queue_file`.

`name_of_analysis` will be the label for the final analysis graph and text output.

`queue_file` should be a completed benchmarking queue file that contains all the tests you want to compare.

It is suggested you keep benchmarking queue files in the queues directory but they can be kept anywhere.

`[-b] [-e] [-v]` are optional flags that determine what type of analyses are done on the runs. These flags are detailed in the output section.

At least one of these flags must be enabled to do any analysis.

## Output

Progress will be kept in records.txt and analysis results will be saved in the analyses directory under a uuid.

The uuid for the analysis will be printed to stdout after the program runs.

Bugs are classified according to the current config.

### Bug Graph Analysis, `[-b]`

Enabling this option will enable outputting a file called bug_graph.png into the analysis folder.

The bug_graph.png file has two graphs which compare all the queued tests. It has a figure for bugs over time and a figure for bugs over generations.

### Edge Graphs Analysis, `[-e]`

Enabling this option will enable outputting files called edge_{target}.png into the analysis folder for every target enabled in all of the queued tests.

Each edge_{target}.png has two graphs in it which compare all the queued tests.

It has a figure for edges covered over time for that target and a figure for edges covered over generation for that target.

### Overlap Analysis, `[-v]`

Enabling this option will enable outputting a file called overlap_summary.txt and a file called overlap_machine.csv into the analysis folder.

The overlap_summary.txt file groups every found bug by the largest set of queued tests that commonly found it.

In descending order, by way of number of queued tests that commonly found them, it has human readable representations of all the groups.

The overlap_machine.csv file tracks the number of bugs commonly found by every possible combination of queued tests. Single bugs can be counted in multiple groups.

Each row represents one such group. Every row will start with a series of True, False values. True indicates that the bugs in the group were commonly found in the corresponding queued test for that column.

The final column of the data contains the number of bugs that fit into each group.
