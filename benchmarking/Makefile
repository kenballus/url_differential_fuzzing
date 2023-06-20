.PHONY: all format typecheck lint
all: analyses bench_configs benchmark_queue format typecheck lint

analyses:
	mkdir analyses

bench_configs:
	mkdir bench_configs

benchmark_queue:
	touch benchmark_queue

format:
	black -l 110 *.py

typecheck:
	mypy --check-untyped-defs analyze.py

lint:
	pylint --disable=line-too-long,missing-module-docstring,invalid-name,missing-function-docstring,missing-class-docstring,consider-using-with,too-many-locals,too-many-branches,import-error,wrong-import-position *.py