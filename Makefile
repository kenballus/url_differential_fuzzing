.PHONY: all clean
all: clean format typecheck
	python3 diff_fuzz.py

format:
	black diff_fuzz.py
	black config.py

typecheck:
	mypy diff_fuzz.py

clean:
	rm -rf traces inputs
	mkdir traces
	mkdir inputs
