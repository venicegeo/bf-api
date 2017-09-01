#!/bin/bash

cd $(dirname $(dirname $0))  # Return to root

cd migrations/vendor/

if [ ! -f jre/bin/java ]; then
  echo "Expected migrations/vendor/jre/bin/java, but not found"
  exit 1
fi

if [ ! -f liquibase.jar ]; then
  echo "Expected migrations/vendor/liquibase.jar, but not found"
  exit 1
fi

if [ ! -f postgresql.jar ]; then
  echo "Expected migrations/vendor/postgresql.jar, but not found"
  exit 1
fi

JAVA_BIN_DIR="$(cd "$(dirname jre/bin/java)"; pwd -P)"
PATH=$JAVA_BIN_DIR:$PATH

cd ..

python migrate.py \
  --changelog ./changelog.xml \
  --liquibase vendor/liquibase.jar \
  --classpath vendor/postgresql.jar \
  update

PORT=$1
PORT=${PORT:-8080}

gunicorn bfapi.server:server --pythonpath .. --threads 5 -b 0.0.0.0:$PORT
