#!/usr/bin/env bash

source /vagrant/.dev/environment-vars.sh

# Set certs needed for fake geoaxis
export SSL_CERT=/vagrant/.dev/ssl-certificate.pem
export SSL_KEY=/vagrant/.dev/ssl-certificate.key

# Run it
env GEOAXIS=localhost:5001 GEOAXIS_CLIENT_ID=abc GEOAXIS_SECRET=123 \
  HOST=0.0.0.0 PORT=5001 \
  nohup /vagrant/.env/bin/python \
  /vagrant/.fake_geoaxis/fake_geoaxis.py &> /vagrant/vagrant-geoaxis.log &

echo "Started fake GeoAxis."
echo "Starting main API..."

. /vagrant/vagrant/vagrant-start.sh

exit 0
