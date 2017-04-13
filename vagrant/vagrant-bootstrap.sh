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
psql -c "CREATE ROLE beachfront WITH LOGIN PASSWORD 'secret'"
psql -c "CREATE DATABASE beachfront WITH OWNER beachfront"
psql beachfront -c "CREATE EXTENSION postgis"
sudo service postgresql restart

# Install GeoServer
sudo add-apt-repository -y ppa:openjdk-r/ppa
sudo apt-get -y update
sudo apt-get -y install openjdk-8-jdk tomcat7 unzip
# Ensure Tomcat is pointing to JDK8
sudo echo 'JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-amd64' >> /etc/default/tomcat7
# Download and Install
wget http://sourceforge.net/projects/geoserver/files/GeoServer/2.8.2/geoserver-2.8.2-war.zip
unzip geoserver-2.8.2-war.zip geoserver.war
sudo mv geoserver.war /var/lib/tomcat7/webapps/
sudo service tomcat7 restart

# Create the development environment. Ensure proper EOL encoding (thank you Windows)
sudo apt-get -y install dos2unix
find /vagrant -type f -print0 | xargs -0 dos2unix
/vagrant/scripts/create-development-environment.sh

# Run Tests
/vagrant/scripts/test.sh

# Start the application
/vagrant/scripts/run-in-development-mode.sh
