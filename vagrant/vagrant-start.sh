#!/usr/bin/env bash

sudo service postgresql restart
sudo service tomcat7 restart

# Run Tests
echo "Running application unit tests..."
/vagrant/scripts/test.sh

echo "Tests run. Starting application..."
# Start the application
nohup /vagrant/scripts/run-in-development-mode.sh &> /vagrant/vagrant-start.log &

exit 0
