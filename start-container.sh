app_id=`docker ps | grep docker_frappe | awk {'print $1'}`

docker exec -it $app_id bash -c 'cd /home/frappe/frappe-bench && su frappe; exec "${SHELL:-sh}"'
