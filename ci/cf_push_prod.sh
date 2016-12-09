#!/bin/bash -ex

export PIAZZA_URL=https://piazza.geointservices.io/key
export MANIFEST_FILENAME=manifest.prod.yml

./ci/_cf_push.sh
