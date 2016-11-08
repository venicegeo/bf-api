#!/bin/bash

cd $(dirname $(dirname $0))  # Return to root

# Enter virtual environment
. .env/bin/activate

# Collect environment variables
if [ ! -f .environment-vars.dev.sh ]; then
    echo "Missing .environment-vars.dev.sh file: Check the README for instructions on how to create this file."
    exit 1
fi
. .environment-vars.dev.sh

if [ "${PORT}" == "" ]; then
    echo "PORT cannot be blank. Please set a value and try running this script again."
    exit 1
fi

gunicorn bfapi.server:server \
  -b localhost:${PORT} \
  --reload \
  --worker-class aiohttp.worker.GunicornWebWorker
