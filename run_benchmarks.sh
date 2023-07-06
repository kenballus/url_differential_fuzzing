#!/bin/bash

# Go to the correct folder
cd $(dirname $0)

use_statement() {
    echo "Use: run_benchmarks.sh -n name_of_analysis [-b] [-e] [-v] < queue_file"
    echo "  -n name_of_analysis -> The Name to attribute to the resulting Analysis"
    echo "  -b -> Enables the Creation of Bug Graph in Analysis"
    echo "  -e -> Enables the Creation of Edge Graphs in Analysis"
    echo "  -v -> Enables the Creation of Overlap Reports in Analysis"
    echo "  queue_file -> The File to draw runs of the fuzzer from"
    exit 1
}

main (){
    if [ $(basename $0) = "untracked_run_benchmarks.sh" ]
    then
        rm -rf /tmp/diff_fuzz* # Just in case temp files were left from a previous run
        rm -rf benchmarking/reports

        # Save Original Config
        cp config.py benchmarking/original_config.py
        if [ $? -ne 0 ]
        then
            echo "No original config! Try running make in the main directory."
            exit 1
        fi

        # Save original branch
        org_branch=$(git branch --show-current)

        mkdir benchmarking/reports
        echo "Start of new benchmarking run." > benchmarking/records.txt
        echo "-----Running-----"
        run_count=0
        while read line || [ -n "$line" ]
        do
            name=$(echo $line | cut -f 1 -d ,)
            commit=$(echo $line | cut -f 2 -d ,)
            timeout=$(echo $line | cut -f 3 -d ,)
            tcs=$(echo $line | cut -f 4 -d ,)
            echo "-------------------------------------------------------------------" >> benchmarking/records.txt
            echo $name >> benchmarking/records.txt
            echo $commit >> benchmarking/records.txt
            echo $timeout >> benchmarking/records.txt
            echo $tcs >> benchmarking/records.txt
            echo "-------------------------------------------------------------------" >> benchmarking/records.txt
            echo "Running: ${name}"
            # Switch to correct commit
            git checkout $commit >> benchmarking/records.txt
            # Do the run
            if [ "$tcs" = "" ]
            then
                echo "No config specified; copying original config into the config file.." >> benchmarking/records.txt
                cp benchmarking/original_config.py config.py
            else
                echo "Copying ${tcs} into the config file.." >> benchmarking/records.txt
                cp "benchmarking/bench_configs/${tcs}" config.py
            fi
            # Make a folder to output info to
            mkdir benchmarking/reports/${run_count}
            echo -n $name > benchmarking/reports/${run_count}/name.txt
            timeout --foreground --signal=2 $timeout python diff_fuzz.py 1> benchmarking/reports/${run_count}/report.json 2>> benchmarking/records.txt

            let 'run_count++'
        done

        # Go back to the original branch
        git switch $org_branch

        # Bring back orginal config
        cp benchmarking/original_config.py config.py

        # Analysis
        echo "-----Analysis-----"
        python analyze.py $@

        # Clean Up
        rm -rf benchmarking/reports
        rm benchmarking/original_config.py
    else
        echo "Copying script into untracked version"
        cp run_benchmarks.sh untracked_run_benchmarks.sh
        sh untracked_run_benchmarks.sh $@
        rm untracked_run_benchmarks.sh
    fi
}

named=0
test_enabled=0
# Parse Options
while getopts "bven:" opt; do
    case ${opt} in
    n )
    named=1
    ;;
    [b,v,e] )
    test_enabled=1
    ;;
    \? )
    echo "Invalid option: $OPTARG" 1>&2
    ;;
    : )
    echo "Invalid option: $OPTARG requires an argument" 1>&2
    ;;
    esac
done

if [ $named -eq 0 ]; then
    echo "The analysis must be given a name via -n name_of_analysis"
    echo ""
    use_statement
fi

if [ $test_enabled -eq 0 ]; then
    echo "[-b] [-e] or [-v] must be enabled, otherwise no analysis will be performed!"
    echo ""
    use_statement
fi

main "$@"
