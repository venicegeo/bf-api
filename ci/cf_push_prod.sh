#!/bin/bash -ex

export GEOAXIS_DOMAIN=gxisapi.gxaccess.com
export PIAZZA_URL=https://piazza.geointservices.io/v2/key
export MANIFEST_FILENAME=manifest.jenkins.yml

./ci/_cf_push.sh
