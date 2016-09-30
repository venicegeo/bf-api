#!/bin/bash

cd $(dirname $(dirname $0))  # Return to root

python -m unittest
