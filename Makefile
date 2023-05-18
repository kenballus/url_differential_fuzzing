.PHONY: all format typecheck lint
all: format typecheck lint
	python3 diff_fuzz.py

format:
	black -l 110 diff_fuzz.py config.py grammar.py

typecheck:
	mypy diff_fuzz.py

lint:
	pylint --disable=line-too-long,missing-module-docstring,invalid-name,missing-function-docstring,missing-class-docstring,unnecessary-lambda-assignment,consider-using-with,too-many-locals,multiple-statements,protected-access,too-many-branches diff_fuzz.py config.py grammar.py
