#!/bin/bash

cat <(./dbench start) &

sleep 5

while ! [[ $i == 20 ]]
do
    output=$( curl "http://localhost:8000" )
    { echo "Exit status of curl: $?"
    } 1>&2
    sleep 2
    i=$((i + 1))
done


echo "${output}" | grep '<title> Login </title>' || exit 1