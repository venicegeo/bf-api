#!/usr/bin/env bash

# Install Python 3.5 and related dependencies
sudo add-apt-repository -y ppa:fkrull/deadsnakes
sudo apt-get -y update
sudo apt-get -y install python3.5
sudo apt-get -y install python3-pip python3.5-dev
pip3 install virtualenv

# Install Postgres and Postgis
sudo apt-get -y install postgresql postgresql-contrib pgadmin3
sudo apt-get -y install postgis postgresql-9.3-postgis-2.1 libpq-dev
# Give Vagrant user Permissions
sudo -u postgres psql -c "CREATE ROLE beachfront WITH LOGIN PASSWORD 'secret'"
sudo -u postgres psql -c "CREATE DATABASE beachfront WITH OWNER beachfront"
sudo -u postgres psql beachfront -c "CREATE EXTENSION postgis"
sudo service postgresql restart

# Install GeoServer
sudo add-apt-repository -y ppa:openjdk-r/ppa
sudo apt-get -y update
sudo apt-get -y install openjdk-8-jdk tomcat7 unzip
# Ensure Tomcat is pointing to JDK8
sudo echo 'JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-amd64' >> /etc/default/tomcat7
# Download and Install
wget --no-verbose http://sourceforge.net/projects/geoserver/files/GeoServer/2.8.2/geoserver-2.8.2-war.zip
unzip geoserver-2.8.2-war.zip geoserver.war
sudo mv geoserver.war /var/lib/tomcat7/webapps/

sudo service tomcat7 restart
# Create Workspace
sudo curl http://localhost:8080/geoserver/rest/workspaces --user admin:geoserver --header "Content-Type:application/xml" -d "<workspace><name>piazza</name></workspace>"
# Create Datastore
sudo curl http://localhost.dev:8080/geoserver/rest/workspaces/piazza/datastores --user admin:geoserver --header "Content-Type:application/xml" -d '<dataStore><name>piazza</name><description>piazza</description><type>PostGIS</type><enabled>true</enabled><workspace><name>piazza</name></workspace><connectionParameters><entry key="schema">public</entry><entry key="Evictor run periodicity">300</entry><entry key="Max open prepared statements">50</entry><entry key="encode functions">false</entry><entry key="preparedStatements">false</entry><entry key="database">beachfront</entry><entry key="host">localhost</entry><entry key="Loose bbox">true</entry><entry key="Estimated extends">true</entry><entry key="fetch size">1000</entry><entry key="Expose primary keys">false</entry><entry key="validate connections">true</entry><entry key="Support on the fly geometry simplification">true</entry><entry key="Connection timeout">20</entry><entry key="create database">false</entry><entry key="port">5432</entry><entry key="passwd">secret</entry><entry key="min connections">1</entry><entry key="dbtype">postgis</entry><entry key="namespace">http://radiantblue.com/piazza/</entry><entry key="max connections">10</entry><entry key="Evictor tests per run">3</entry><entry key="Test while idle">true</entry><entry key="user">beachfront</entry><entry key="Max connection idle time">300</entry></connectionParameters><__default>false</__default></dataStore>'

# Create the development environment. Ensure proper EOL encoding (thank you Windows)
sudo apt-get -y install dos2unix
find /vagrant -type f -print0 | xargs -0 dos2unix

# Create environment
/vagrant/scripts/create-development-environment.sh

exit 0
