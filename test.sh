#!/bin/bash

./dbench start > /tmp/bench.log &

curl --retry 20 --retry-delay 1 --retry-connrefused "http://localhost:8000/login" | grep '<title> Login </title>' || exit 1