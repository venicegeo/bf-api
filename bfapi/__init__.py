# Copyright 2016, RadiantBlue Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License. You may obtain a copy of the
# License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import time
from flask import Flask, jsonify
from bfapi import db

import bfapi.config
import bfapi.v0

_time_started = time.time()

################################################################################
# Debugging Info
print('-' * 80)
print()
print('bf-api'.center(80))
print('~~~~~~'.center(80))
print()
for key in ('PZ_GATEWAY', 'CATALOG', 'TIDEPREDICTION'):
    print('{0:>38} : {1}'.format(key, bfapi.config.__dict__[key]))
print()
print('-' * 80)
################################################################################

#
# Configuration
#

server = Flask(__name__)

#
# Attach Routing
#


## TODO -- auth filtering
## TODO -- find way to pass credentials to instance

# Metrics/Health Check
@server.route('/')
def hello():
    uptime = round(time.time() - _time_started, 3)
    return jsonify(uptime=uptime)


server.register_blueprint(bfapi.v0.blueprint, url_prefix='/v0')
