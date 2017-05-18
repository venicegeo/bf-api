#!/bin/bash

cd $(dirname $(dirname $0))  # Return to root

cd migrations/vendor/

if [ ! -f jre8.tar.gz ]; then
  echo "Expected migrations/vendor/jre8.tar.gz, but not found"
  exit 1
fi

if [ ! -f liquibase.tar.gz ]; then
  echo "Expected migrations/vendor/liquibase.tar.gz, but not found"
  exit 1
fi

if [ ! -f postgresql.jar ]; then
  echo "Expected migrations/vendor/postgresql.jar, but not found"
  exit 1
fi

echo "Extracting vendor dependencies..."

tar xf jre8.tar.gz
tar xf liquibase.tar.gz

JAVA_BIN_DIR="$(cd "$(dirname jre*/bin/java)"; pwd -P)"
PATH=$JAVA_BIN_DIR:$PATH

cd ..

python migrate.py \
  --changelog ./changelog.xml \
  --liquibase vendor/liquibase/liquibase \
  --classpath vendor/postgresql.jar \
  update

PORT=$1
PORT=${PORT:-8080}

gunicorn bfapi.server:server --threads 5 -b 0.0.0.0:$PORT
