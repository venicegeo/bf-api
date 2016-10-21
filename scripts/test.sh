#!/bin/bash

cd $(dirname $(dirname $0))  # Return to root

. .env/bin/activate

python -m unittest
