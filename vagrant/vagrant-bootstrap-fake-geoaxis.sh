#!/usr/bin/env bash

# Install Git
sudo apt-get -y install git

[ -e /vagrant/.fake_geoaxis ] && rm -rf /vagrant/.fake_geoaxis
git clone https://github.com/venicegeo/fake_geoaxis.git /vagrant/.fake_geoaxis
