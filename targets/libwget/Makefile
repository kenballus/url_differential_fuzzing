CC := afl-clang-fast
INCLUDE := wget2/include

libwget_target: libwget_target.c wget2/libwget/.libs/libwget.a
	$(CC) -I$(INCLUDE) libwget_target.c wget2/libwget/.libs/libwget.a -o libwget_target

wget2/libwget/.libs/libwget.a: get_wget2.sh
	./get_wget2.sh

.PHONY: clean
clean:
	rm -rf libwget_target wget2