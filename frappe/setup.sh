#USER root
cd /home/frappe
git clone https://github.com/frappe/bench bench-repo
pip install -e bench-repo
apt-get install -y libmysqlclient-dev mariadb-client mariadb-common
chown -R frappe:frappe /home/frappe

#USER frappe
su frappe
