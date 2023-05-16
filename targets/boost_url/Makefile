CXX := afl-clang-fast++
CXXFLAGS := -Weverything -Wno-c++98-compat -Os
IFLAGS := -Iboost

boost_url_target: boost_url_target.cpp boost/boost
	$(CXX) $(IFLAGS) $(CXXFLAGS) boost_url_target.cpp -o boost_url_target

boost/boost: get_boost.sh
	./get_boost.sh

.PHONY: clean
clean:
	rm -rf boost_url_target boost
