#!/bin/bash -ex

export PIAZZA_URL=https://piazza.stage.geointservices.io/key
export MANIFEST_FILENAME=manifest.stage.yml

./ci/_cf_push.sh
