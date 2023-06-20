#!/bin/bash

if [ $# -gt 2 ] || [ $# -lt 1 ]
then
echo "Use: run_benchmarks.sh name_of_analysis"
exit 1
fi

# Go to the correct folder
cd $(dirname $0)

# Arg1 = name of the run
# Arg2 = timeout of the run
do_run () {
    # Go to main folder
    cd ..
    # Run
    timeout --foreground --signal=2 $2 python diff_fuzz.py $1 1> benchmarking/reports/${1}_report.json 2>> benchmarking/records.txt
    # Return
    cd benchmarking
}

main (){
    if [ "$2" = "untracked" ]
    then
        # Collect Data

        rm -rf /tmp/diff_fuzz* # Just in case temp files were left from a previous run
        rm -rf reports

        mkdir reports
        echo "Start of new benchmarking run" > records.txt
        declare -a names_uuids=()
        while read line
        do
            name=$(echo $line | cut -f 1 -d ,)
            commit=$(echo $line | cut -f 2 -d ,)
            timeout=$(echo $line | cut -f 3 -d ,)
            tcs=$(echo $line | cut -f 4 -d ,)
            uuid=$(uuidgen)
            echo "-------------------------------------------------------------------" >> records.txt
            echo $name >> records.txt
            echo $commit >> records.txt
            echo $timeout >> records.txt
            echo $tcs >> records.txt
            echo $uuid >> records.txt
            echo "-------------------------------------------------------------------" >> records.txt
            names_uuids+=("${name}" ${uuid})
            # Switch to correct commit
            # git reset --hard >> records.txt
            # git checkout $commit >> records.txt
            # git reset --hard >> records.txt
            # Do the run
            if [ "$tcs" = "" ]
            then
                do_run ${uuid} ${timeout}
            else
                echo "Copying ${tcs} into the config file.." >> records.txt
                cat "bench_configs/${tcs}" > ../config.py
                do_run ${uuid} ${timeout}
            fi
        done < benchmark_queue

        # Analysis
        echo ANALYSIS
        python analyze.py "${1}" "${names_uuids[@]}"

        # Clean Up
        rm -rf reports
    else
        echo "Copying Script into Untracked Version"
        cp run_benchmarks.sh untracked_run_benchmarks.sh
        sh untracked_run_benchmarks.sh "${1}" untracked
        rm untracked_run_benchmarks.sh
    fi
}

main "$@"