echo "Enter a password for your database "
read DB_PASS

echo 'export DB_PASS='$DB_PASS >> ~/.bashrc
source ~/.bashrc

docker-compose up -d
app_id=`docker ps | grep docker_frappe | awk {'print $1'}`

docker exec -it $app_id bash -c './setup.sh; exec "${SHELL:-sh}"'
