#!/bin/bash

rm -rf /tmp/diff_fuzz* # Just in case temp files were left from a previous run
cat benchmarking/benchmarks | while read line
do
    name=$(echo $line | awk '{print $1}')
    commit=$(echo $line | awk '{print $2}')
    echo $name
    echo $commit
    # Switch to correct commit
    git checkout $commit
    # Run
    python diff_fuzz.py $name 1> benchmarking/$name.json
    # Gather Data
    cp -r results/$name benchmarking/$name
done