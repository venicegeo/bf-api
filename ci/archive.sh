#!/bin/bash -ex

pushd `dirname $0`/.. > /dev/null
root=$(pwd -P)
popd > /dev/null

source $root/ci/vars.sh

## Install Dependencies ########################################################

# Create or enter virtual environment
if [ ! -f .env/bin/activate ]; then
    virtualenv .env
fi
. .env/bin/activate

# Fetch libraries
mkdir -p vendor
.env/bin/pip install -d vendor -r requirements.txt

## DB migration process depenendencies
mkdir -p migrations/vendor

# Liquibase 3.2.2
wget https://repo1.maven.org/maven2/org/liquibase/liquibase-core/3.2.2/liquibase-core-3.2.2.jar \
  -O migrations/vendor/liquibase.jar

# PostgreSQL JDBC 42.0.0

wget https://jdbc.postgresql.org/download/postgresql-42.0.0.jre6.jar \
  -O migrations/vendor/postgresql.jar

# Java 8 u131
wget http://javadl.oracle.com/webapps/download/AutoDL?BundleId=220305_d54c1d3a095b4ff2b6607d096fa80163 \
  -O - | \

tar xz --directory migrations/vendor

if [ -d migrations/vendor/jre ]; then
  rm -rf migrations/vendor/jre
fi
mv migrations/vendor/jre* migrations/vendor/jre
chmod -R a+rw migrations/vendor/jre

## Build #######################################################################

target_files="
bfapi/
migrations/
vendor/
scripts/cf-migrate-and-run.sh
sql/
Procfile
requirements.txt
runtime.txt
"

tar cvfz ${APP}.${EXT} ${target_files}
