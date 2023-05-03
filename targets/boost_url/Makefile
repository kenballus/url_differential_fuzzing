CXX := afl-clang-fast++
CXXFLAGS := -Weverything -Wno-c++98-compat -Os
INCLUDE := boost/libs/url/include/boost

boost_url_target: boost_url_target.cpp boost/libs/url/include/boost/url/src.hpp
	$(CXX) $(CXXFLAGS) -I$(INCLUDE) boost_url_target.cpp -o boost_url_target

boost/libs/url/include/boost/url/src.hpp: get_boost_url.sh
	git clone --recurse-submodules https://github.com/boostorg/boost.git

.PHONY: clean
clean:
	rm -rf boost_url_target boost
