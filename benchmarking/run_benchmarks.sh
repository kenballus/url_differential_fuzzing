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
        rm -rf /tmp/diff_fuzz* # Just in case temp files were left from a previous run
        rm -rf reports

        # Save Original Config
        cp ../config.py original_config.py
        if [ $? -ne 0 ]
        then
            echo "No Original Config! Try running make in the main directory."
            exit 1
        fi

        # Save original branch
        org_branch=$(git branch --show-current)

        mkdir reports
        echo "Start of new benchmarking run" > records.txt
        echo "-----Running-----"
        declare -a names_uuids=()
        while read line || [ -n "$line" ]
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
            echo "Running: ${name}"
            # Switch to correct commit
            git reset --hard >> records.txt
            git checkout $commit >> records.txt
            git reset --hard >> records.txt
            # Do the run
            if [ "$tcs" = "" ]
            then
                echo "No Config Specified, Copying Original Config into the config file.." >> records.txt
                cp original_config.py ../config.py
                do_run ${uuid} ${timeout}
            else
                echo "Copying ${tcs} into the config file.." >> records.txt
                cp "bench_configs/${tcs}" ../config.py
                do_run ${uuid} ${timeout}
            fi
        done

        # Go back to the original branch
        git switch $org_branch

        # Bring back orginal config
        cp original_config.py ../config.py

        # Analysis
        echo "-----Analysis-----"
        python analyze.py "${1}" "${names_uuids[@]}"

        # Clean Up
        rm -rf reports
        rm original_config.py
    else
        echo "Copying Script into Untracked Version"
        cp run_benchmarks.sh untracked_run_benchmarks.sh
        sh untracked_run_benchmarks.sh "${1}" untracked
        rm untracked_run_benchmarks.sh
    fi
}

main "$@"