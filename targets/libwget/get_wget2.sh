#!/bin/sh

pushd $(dirname $0)

rm -rf wget2 && \
git clone https://gitlab.com/gnuwget/wget2.git && \
cd wget2 && ./bootstrap && \
export CC=afl-clang-fast && \
./configure --disable-shared \
            --without-libiconv-prefix \
            --without-included-regex \
            --without-libintl-prefix \
            --without-libpsl \
            --without-libhsts \
            --without-libnghttp2 \
            --without-gpgme \
            --without-zlib \
            --without-brotlidec \
            --without-zstd \
            --without-lzip \
            --without-libidn2 \
            --without-libidn \
            --without-libpcre2 \
            --without-libpcre \
            --without-libmicrohttpd \
            --without-plugin-support && \
make -j$(nproc)

popd
