#!/bin/bash

python -c "from bfapi.service import geoserver; geoserver.install_if_needed()"
