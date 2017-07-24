echo "Enter a password for your database "
read DB_PASS

echo 'export DB_PASS='$DB_PASS >> ~/.bashrc
source ~/.bashrc

docker-compose up -d
