.PHONY: all format typecheck lint benchmarking
all: config format typecheck lint benchmarking
	python3 diff_fuzz.py

config:
	[ -e config.py ] || cp config.defpy config.py

format:
	black -l 110 *.py

typecheck:
	mypy *.py

lint:
	pylint --disable=protected-access,line-too-long,missing-module-docstring,invalid-name,missing-function-docstring,missing-class-docstring,consider-using-with,too-many-locals,too-many-branches *.py

benchmarking:
	[ -e benchmarking ] || mkdir benchmarking
	[ -e benchmarking/bench_configs ] || mkdir benchmarking/bench_configs
	[ -e benchmarking/queues ] || mkdir benchmarking/queues
	[ -e benchmarking/analyses ] || mkdir benchmarking/analyses
