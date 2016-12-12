#!/bin/bash

cd $(dirname $(dirname $0))  # Return to root

# Enter virtual environment
. .env/bin/activate

# Collect environment variables
if [ ! -f .dev/environment-vars.sh ]; then
    echo "Missing .dev/environment-vars.sh.  Have you already run ./scripts/create-development-environment.sh ?"
    exit 1
fi
. .dev/environment-vars.sh

if [ "${PORT}" == "" ]; then
    echo "PORT cannot be blank. Please set a value and try running this script again."
    exit 1
fi

gunicorn bfapi.server:server \
  -b localhost:${PORT} \
  --threads 5 \
  --keyfile .dev/ssl-certificate.key \
  --certfile .dev/ssl-certificate.pem \
  --reload
