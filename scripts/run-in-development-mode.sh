#!/bin/bash

cd $(dirname $(dirname $0))  # Return to root

FLASK_DEBUG=1 FLASK_APP=bfapi/__init__.py flask run
