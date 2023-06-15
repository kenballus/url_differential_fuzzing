# Benchmarking Instructions

## Set-Up

From the benchmarking directory

Run:

```make```

## Basic Use

In the benchmarking_queue file. Tests can be added as followed.

```TestName CommitNumber Optional[configfile]```

Each test's results will be saved into ```runs/TestName```

Each Test will be run on ```CommitNumber``` with config ```configfile```

If no config file is specified each test will be run on the same config file as the test before it. If it is the first test it will be run on the current config file.

Example:

```QueueTest cdab061f174edc301a3fab1c78c5440630d0fbe5 QueueTestConfig.py```

Each test must be followed by a new line character in the file.

A complete benchmarking_queue file should be in the same format as follows:

```
BaseMultipleBytes e7823b0c4cba1d79901f3db50560dcaad8eb90f4 largeByte.py
TestMultipleBytes aa517f562e3138a751a0cf6aa0731134a7fedb1d largeByte.py
TestCombinedMini 7cfc15c1ec954da782daa5a7f69d51439c1262ac combined.py
BaseCombinedMini e4784f7824696825e987c5c2816c0d07850b6b65 combined.py

```

## Analysis