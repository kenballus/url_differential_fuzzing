#!/bin/bash

# Go to the correct folder
cd $(dirname $0)

# Arg1 = targetconfig file to draw from
select_targets () {
    echo "Selecting Targets From: ${1}" >> records.txt
    cutoff=$(cat ../config.py | grep TARGET_CONFIG -n | tail -1 | grep -Eo "[0-9]+:" | grep -Eo "[0-9]+")
    stopline=$(expr ${cutoff} - 1)
    cat ../config.py | head -${stopline} > temp_target_select.py
    cat $1 >> temp_target_select.py
    cp temp_target_select.py ../config.py
    rm temp_target_select.py
}

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
            if [ "$tcs" = "standards" ]
            then
                for config_name in standard_targets/*
                do
                    select_targets $config_name
                    do_run ${name}_$(basename $config_name)
                done
            elif [ "$tcs" = "" ]
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