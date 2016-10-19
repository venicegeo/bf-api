#!/bin/bash

cd $(dirname $(dirname $0))  # Return to root

gunicorn bfapi:server \
  -b localhost:5000 \
  --reload \
  --worker-class aiohttp.worker.GunicornWebWorker \
  --access-logfile /dev/stdout \
  --error-logfile /dev/stderr \
  --access-logformat '%a %l %t "%r" %s %b'
