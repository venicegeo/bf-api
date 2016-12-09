#!/bin/bash -ex

export PIAZZA_URL=https://piazza.int.geointservices.io/key
export MANIFEST_FILENAME=manifest.int.yml

./ci/_cf_push.sh
