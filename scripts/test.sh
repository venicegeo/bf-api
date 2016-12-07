#!/bin/bash

cd $(dirname $(dirname $0))  # Return to root

. .env/bin/activate

coverage run --source=bfapi -m unittest discover
coverage report
