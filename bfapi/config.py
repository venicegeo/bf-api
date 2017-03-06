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
_errors = []
def validate(failfast: bool = True):
    if not DOMAIN: _errors.append('DOMAIN cannot be blank')
    if not UI: _errors.append('UI cannot be blank')
    if not SECRET_KEY: _errors.append('SECRET_KEY cannot be blank')
    if not PIAZZA_API_KEY: _errors.append('PIAZZA_API_KEY cannot be blank')
    if not POSTGRES_HOST: _errors.append('POSTGRES_HOST cannot be blank')
    if not POSTGRES_PORT: _errors.append('POSTGRES_PORT cannot be blank')
    if not POSTGRES_DATABASE: _errors.append('POSTGRES_DATABASE cannot be blank')
    if not POSTGRES_USERNAME: _errors.append('POSTGRES_USERNAME cannot be blank')
    if not POSTGRES_PASSWORD: _errors.append('POSTGRES_PASSWORD cannot be blank')
    if not GEOSERVER_HOST: _errors.append('GEOSERVER_HOST cannot be blank')
    if not GEOSERVER_USERNAME: _errors.append('GEOSERVER_USERNAME cannot be blank')
    if not GEOSERVER_PASSWORD: _errors.append('GEOSERVER_PASSWORD cannot be blank')
    if not GEOAXIS: _errors.append('GEOAXIS cannot be blank')
    if not GEOAXIS_CLIENT_ID: _errors.append('GEOAXIS_CLIENT_ID cannot be blank')
    if not GEOAXIS_SECRET: _errors.append('GEOAXIS_SECRET cannot be blank')

    if not _errors:
        return

    error_message = 'Configuration error:\n{}'.format('\n'.join(['\t* ' + s for s in _errors]))
    if failfast:
        print('!' * 80, error_message, '!' * 80, sep='\n\n', file=sys.stderr, flush=True)
        os.kill(os.getppid(), signal.SIGQUIT)
        signal.pause()
        exit(1)
    else:
        raise Exception(error_message)

def _getservices() -> dict:
    def collect(node: dict):
        for k, v in node.items():
            path.append(k)
            if isinstance(v, dict):
                collect(v)
            else:
                services['.'.join(path)] = v
            path.pop()

    services = {}
    path = []

    vcap_services = os.getenv('VCAP_SERVICES')
    if not vcap_services:
        _errors.append('VCAP_SERVICES cannot be blank')
        return services

    try:
        vcap_dict = json.loads(vcap_services)
        for key in vcap_dict.keys():
            for user_service in vcap_dict[key]:
                path.append(user_service['name'])
                collect(user_service)
                path.pop()
    except TypeError as err:
        _errors.append('In VCAP_SERVICES: encountered malformed entry: {}'.format(err))
    except KeyError as err:
        _errors.append('In VCAP_SERVICES: some entry is missing property {}'.format(err))
    except json.JSONDecodeError as err:
        _errors.append('In VCAP_SERVICES: invalid JSON: {}'.format(err))
    except Exception as err:
        _errors.append('In _getservices: {}'.format(err))
    return services
################################################################################

DOMAIN = os.getenv('DOMAIN', 'localdomain')

_normalized_domain = DOMAIN.replace('int.', 'stage.')

PIAZZA       = os.getenv('PIAZZA', 'piazza.' + _normalized_domain)
CATALOG      = os.getenv('CATALOG', 'bf-ia-broker.' + _normalized_domain)
UI           = os.getenv('UI', 'beachfront.' + _normalized_domain)

PIAZZA_API_KEY = os.getenv('PIAZZA_API_KEY')
SECRET_KEY     = os.getenv('SECRET_KEY', os.urandom(24).hex())

GEOAXIS           = os.getenv('GEOAXIS')
GEOAXIS_CLIENT_ID = os.getenv('GEOAXIS_CLIENT_ID')
GEOAXIS_SECRET    = os.getenv('GEOAXIS_SECRET')

JOB_WORKER_INTERVAL = timedelta(seconds=60)
JOB_TTL = timedelta(hours=2)
SESSION_TTL = timedelta(minutes=30)

_services = _getservices()

POSTGRES_HOST = _services.get('pz-postgres.credentials.hostname')
POSTGRES_PORT = _services.get('pz-postgres.credentials.port')
POSTGRES_DATABASE = _services.get('pz-postgres.credentials.database')
POSTGRES_USERNAME = _services.get('pz-postgres.credentials.username')
POSTGRES_PASSWORD = _services.get('pz-postgres.credentials.password')

GEOSERVER_HOST = _services.get('pz-geoserver-efs.credentials.host')
GEOSERVER_USERNAME = _services.get('pz-geoserver-efs.credentials.username')
GEOSERVER_PASSWORD = _services.get('pz-geoserver-efs.credentials.password')
