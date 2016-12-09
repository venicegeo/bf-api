#!/bin/bash -ex

pushd `dirname $0`/.. > /dev/null
root=$(pwd -P)
popd > /dev/null

source $root/ci/vars.sh

## Install Dependencies ########################################################

# HACK -- workaround for Python 3.5 in Jenkins
if [ $JENKINS_HOME ]; then
    . /opt/rh/rh-python35/enable
fi

# Create or enter virtual environment
if [ ! -f .env/bin/activate ]; then
    virtualenv --python=python3.5 .env
fi
. .env/bin/activate

# Fetch libraries
mkdir -p vendor
pip install -d vendor -r requirements.txt


## Build #######################################################################

target_files="
bfapi/
vendor/
sql/
Procfile
requirements.txt
runtime.txt
"

zip -r ${APP}.${EXT} ${target_files}
