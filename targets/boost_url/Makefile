AFL_ROOT:= /home/bkallus/fuzzing/AFLplusplus/
CXX := $(AFL_ROOT)/afl-clang++
CXXFLAGS := -Weverything -Wno-c++98-compat -Os
INCLUDE := ./url/include

boost_url_target: boost_url_target.cpp
	$(CXX) $(CXXFLAGS) -I$(INCLUDE) boost_url_target.cpp -o boost_url_target

.PHONY: clean
clean:
	rm -f boost_url_target
