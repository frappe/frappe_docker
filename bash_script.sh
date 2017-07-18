docker-compose up -d
db_id=`docker ps | grep "mariadb" | awk '{print $1}'`
db_ip=`docker inspect --format '{{ .NetworkSettings.Networks.docker_default.IPAddress }}' $db_id`
app_id=`docker ps | grep docker_frappe | awk {'print $1'}`
app_ip=`docker inspect --format '{{ .NetworkSettings.Networks.docker_default.IPAddress }}' $app_id`
echo 'export app_id='$app_id >> ~/.bashrc
source ~/.bashrc
echo 'cd ../' >> ./bash_for_container.sh
echo 'bench init frappe-bench && cd frappe-bench' >> ./bash_for_container.sh
echo 'bench set-mariadb-host '$db_ip >> ./bash_for_container.sh
echo 'bench new-site site1' >> bash_for_container.sh 
echo 'bench --site site1 install-app erpnext' >> bash_for_container.sh
echo 'bench start' >> bash_for_container.sh
docker cp bash_for_container.sh $app_id:/home/frappe/code
docker exec -it $app_id bash -c 'cd /home/frappe/code; exec "${SHELL:-sh}"'
