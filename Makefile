.PHONY: all clean
all: clean
	black -l 110 diff_fuzz.py
	mypy diff_fuzz.py
	python3 diff_fuzz.py

clean:
	rm -rf traces inputs
	mkdir traces
	mkdir inputs
