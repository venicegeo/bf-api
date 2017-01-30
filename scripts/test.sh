#!/bin/bash

cd $(dirname $(dirname $0))  # Return to root

. .env/bin/activate

set -a
. test/fixtures/environment-vars.test.sh
set +a

coverage run --source=bfapi -m unittest
coverage report
