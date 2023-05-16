#!/bin/bash

git clone --recurse-submodules "https://github.com/boostorg/boost.git" && cd boost && ./bootstrap.sh && ./b2
