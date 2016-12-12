#!/bin/bash -ex

export PIAZZA_URL=https://piazza.int.geointservices.io/key
export MANIFEST_FILENAME=manifest.int.yml

./ci/_cf_push.sh

# HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
# FIXME - Remove after moving away from legacy image catalog harvest workflow
echo "    SKIP_PRODUCTLINE_INSTALL: 1" >> $MANIFEST_FILENAME
# HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
