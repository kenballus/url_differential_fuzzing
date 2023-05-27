#!/bin/sh
[ ! -d ada ] && git clone "https://github.com/ada-url/ada" && cd ada && python3 singleheader/amalgamate.py
