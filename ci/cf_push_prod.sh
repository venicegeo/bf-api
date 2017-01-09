#!/bin/bash -ex

export GEOAXIS_DOMAIN=gxisaccess.gxaccess.com
export PIAZZA_URL=https://piazza.geointservices.io/v2/key
export MANIFEST_FILENAME=manifest.prod.yml

./ci/_cf_push.sh
