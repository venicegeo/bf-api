#!/bin/bash -ex

pushd `dirname $0`/.. > /dev/null
root=$(pwd -P)
popd > /dev/null

source $root/ci/vars.sh

## Install Dependencies ########################################################

# Create or enter virtual environment
if [ ! -f .env/bin/activate ]; then
  virtualenv --python=python3.5 .env
fi
. .env/bin/activate

# Fetch libraries
mkdir -p vendor
pip download -d vendor -r requirements.txt


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
