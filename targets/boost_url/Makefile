CXX := afl-clang-fast++
CXXFLAGS := -Weverything -Wno-c++98-compat -Os
INCLUDE := boost/libs/url/include,boost/libs/beast/include

boost_url_target: boost_url_target.cpp boost
	$(CXX) -I$(INCLUDE) $(CXXFLAGS) boost_url_target.cpp -o boost_url_target

boost:
	git clone --recurse-submodules https://github.com/boostorg/boost.git

.PHONY: clean
clean:
	rm -rf boost_url_target boost
