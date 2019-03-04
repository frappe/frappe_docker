#!/bin/bash

./dbench start > /tmp/bench.log &

output=$(
  while ! curl "http://localhost:8000/login"
  do
      { echo "Exit status of curl: $?"
      } 1>&2
      sleep 1
  done
)

echo "${output}" | grep '<title> Login </title>' || exit 1