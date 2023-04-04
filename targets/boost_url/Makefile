CXX := afl-clang-fast++
CXXFLAGS := -Weverything -Wno-c++98-compat -Os
INCLUDE := ./url/include

boost_url_target: boost_url_target.cpp url/include/boost/url/src.hpp
	$(CXX) $(CXXFLAGS) -I$(INCLUDE) boost_url_target.cpp -o boost_url_target

url/include/boost/url/src.hpp: get_boost_url.sh
	./get_boost_url.sh

.PHONY: clean
clean:
	rm -f boost_url_target
