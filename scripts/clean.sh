#!/bin/bash

cd $(dirname $(dirname $0))  # Return to root

echo "Cleaning up"
rm -rfv bf-api.zip vendor report .coverage manifest.{dev,int,stage,prod}.yml
