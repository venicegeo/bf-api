#!/bin/bash -ex

pushd `dirname $0`/.. > /dev/null
root=$(pwd -P)
popd > /dev/null

source $root/ci/vars.sh

## Install Dependencies ########################################################

# Create or enter virtual environment
if [ ! -f .env/bin/activate ]; then
    if [ $(uname) == "Darwin" ]; then
        virtualenv --python=python3.5 .env
    else
        # HACK -- workaround for Python 3.5 in Jenkins
        . /opt/rh/rh-python35/enable
        virtualenv --python=python35 .env
    fi
fi
. .env/bin/activate

pip install -r requirements.txt

## Run Tests ###################################################################

coverage run --source=bfapi -m unittest discover
coverage xml -o report/coverage/coverage.xml
coverage html -d report/coverage/html
coverage report
