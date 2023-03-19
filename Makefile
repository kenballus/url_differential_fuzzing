.PHONY: all clean
all: clean format typecheck
	python3 diff_fuzz.py

format:
	black -l 110 diff_fuzz.py
	black -l 110 config.py

typecheck:
	mypy diff_fuzz.py

clean:
	rm -rf traces inputs
	mkdir traces
	mkdir inputs
