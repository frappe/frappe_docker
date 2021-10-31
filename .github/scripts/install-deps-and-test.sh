#!/bin/bash

set -e

sudo apt-get install -y w3m

./tests/check-format.sh
./tests/docker-test.sh

# This is done to not to rebuild images in the next step
git clean -fdx