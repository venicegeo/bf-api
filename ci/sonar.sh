#!/bin/bash -ex

pushd `dirname $0`/.. > /dev/null
root=$(pwd -P)
popd > /dev/null

source $root/ci/vars.sh

## Install Dependencies ########################################################

# Enter virtual environment
if [ ! -f .env/bin/activate ]; then
  virtualenv --python=python3.5 .env
fi
. .env/bin/activate

pip install -r requirements.txt

## Run Tests ###################################################################

coverage run --source=bfapi -m unittest discover
coverage xml -o report/coverage/coverage.xml
coverage html -d report/coverage/html
