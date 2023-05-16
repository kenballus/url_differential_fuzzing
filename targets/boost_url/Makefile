CXX := afl-clang-fast++
CXXFLAGS := -Weverything -Wno-c++98-compat -Os
IFLAGS := -Iboost/libs/url/include -Iboost/libs/beast/include -Iboost/libs/config/include

boost_url_target: boost_url_target.cpp boost
	$(CXX) $(IFLAGS) $(CXXFLAGS) boost_url_target.cpp -o boost_url_target

boost:
	git clone --recurse-submodules https://github.com/boostorg/boost.git

.PHONY: clean
clean:
	rm -rf boost_url_target boost
