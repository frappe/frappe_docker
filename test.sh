#!/bin/bash

docker container ls | grep -i frappe
docker container ls | grep -i redis-cache
docker container ls | grep -i redis-queue
docker container ls | grep -i redis-socketio
docker container ls | grep -i mariadb

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