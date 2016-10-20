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

import json
import os
import sys
import signal
from datetime import timedelta

################################################################################
# Helpers
def _failfast(error_message: str) -> None: print('!' * 80, 'Configuration error: ' + error_message, '!' * 80, sep='\n\n', file=sys.stderr); os.kill(os.getppid(), signal.SIGQUIT); exit(1)
def _sibling_node(subdomain: str) -> str: return '{}.{}'.format(subdomain, os.getenv('DOMAIN', 'localhost').replace('int.', 'stage.'))
def _vcap_service_property(service_name: str, key: str) -> str:
    vcap_services = os.getenv('VCAP_SERVICES')
    if not vcap_services:
        _failfast('VCAP_SERVICES cannot be blank')
    try:
        for service in json.loads(vcap_services)['user-provided']:
            if service['name'] == service_name:
                credentials = service['credentials']
                if not isinstance(credentials, dict):
                    _failfast('`VCAP_SERVICES.user-provided.{}.credentials` is malformed'.format(service_name))
                value = credentials[key]
                if not value:
                    _failfast('`VCAP_SERVICES.user-provided.{}.credentials.{}` is empty'.format(service_name, key))
                return value
        _failfast('service `{}` not found in `VCAP_SERVICES.user-provided`'.format(service_name))
    except KeyError as err:
        _failfast('in VCAP_SERVICES, some node is missing property {}'.format(err))
    except Exception as err:
        _failfast('in VCAP_SERVICES, {}'.format(err))
################################################################################

DEBUG_MODE = os.getenv('DEBUG_MODE') == '1'

PZ_GATEWAY   = os.getenv('PZ_GATEWAY', _sibling_node('pz-gateway'))
CATALOG      = os.getenv('CATALOG', _sibling_node('pzsvc-image-catalog'))
TIDE_SERVICE = os.getenv('TIDE_SERVICE', _sibling_node('bf-tideprediction'))

SYSTEM_AUTH_TOKEN = os.getenv('SYSTEM_AUTH_TOKEN')
JOB_WORKER_INTERVAL = timedelta(seconds=60)
JOB_TTL = timedelta(seconds=900)

POSTGRES_HOST = _vcap_service_property('pz-postgres', 'hostname')
POSTGRES_PORT = _vcap_service_property('pz-postgres', 'port')
POSTGRES_DATABASE = _vcap_service_property('pz-postgres', 'database')
POSTGRES_USERNAME = _vcap_service_property('pz-postgres', 'username')
POSTGRES_PASSWORD = _vcap_service_property('pz-postgres', 'password')
