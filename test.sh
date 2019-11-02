#!/bin/bash

docker container ls | grep frappe
docker container ls | grep mariadb
docker container ls | grep redis-cache
docker container ls | grep redis-queue
docker container ls | grep redis-socketio

cat <(./dbench start) &

while ! [[ $i == 20 ]]
do
    output=$( curl "http://localhost:8000" )
    { echo "Exit status of curl: $?"
    } 1>&2
    sleep 2
    i=$((i + 1))
    echo "${output}" | grep '<title> Login </title>' && exit
done

if ! [[ "$?" == 0 ]]; then exit 1; fi
