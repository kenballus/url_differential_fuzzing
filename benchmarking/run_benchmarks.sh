#!/bin/bash

# Go to the correct folder
cd $(dirname $0)

# Arg1 = name of the run
do_run () {
    # Clear previous folder if it exists
    rm -rf runs/$1
    # Make folder to hold results
    mkdir -p runs/$1 >> records.txt
    # Go to main folder
    cd ..
    # Run
    timeout --signal=2 15 python diff_fuzz.py $1 1> benchmarking/runs/$1/report.json 2>> benchmarking/records.txt
    # Return
    cd benchmarking
    # Gather Data
    cp -r ../results/$1 runs/$1/differentials
}

main (){
    if [ "$1" = "untracked" ]
    then
        rm -rf /tmp/diff_fuzz* # Just in case temp files were left from a previous run
        echo "Start of new benchmarking run" > records.txt
        cat benchmark_queue | while read line
        do
            name=$(echo $line | awk '{print $1}')
            commit=$(echo $line | awk '{print $2}')
            tcs=$(echo $line | awk '{print $3}')
            echo "-------------------------------------------------------------------" >> records.txt
            echo $name >> records.txt
            echo $commit >> records.txt
            echo $tcs >> records.txt
            echo "-------------------------------------------------------------------" >> records.txt        
            # Switch to correct commit
            git reset --hard >> records.txt
            git checkout $commit >> records.txt
            git reset --hard >> records.txt
            # Do the run
            if [ "$tcs" = "" ]
            then
                do_run ${name}
            else
                echo "Copying ${tcs} into the config file.." >> records.txt
                cat "bench_configs/${tcs}" > ../config.py
                do_run ${name}
            fi
        done
    else
        echo "Copying Script into Untracked Version"
        cp run_benchmarks.sh untracked_run_benchmarks.sh
        sh untracked_run_benchmarks.sh untracked
        rm untracked_run_benchmarks.sh
    fi
}

main $1