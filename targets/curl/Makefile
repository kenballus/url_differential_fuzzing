CC := afl-clang-fast
INCLUDE := curl/include

curl_target: curl_target.c curl/lib/.libs/libcurl.a
	$(CC) _I$(INCLUDE) curl_target.c curl/lib/.libs/libcurl.a -o curl_target

curl/lib/.libs/libcurl.a: get_curl.sh
	./get_curl.sh

.PHONY: clean
clean:
	rm -rf curl_target