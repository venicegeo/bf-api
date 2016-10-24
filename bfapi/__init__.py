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

import logging
import logging.config
import os

IS_DEBUG_MODE = os.getenv('DEBUG_MODE') == '1'
if IS_DEBUG_MODE:
    print('*' * 80, '\u26A0  SERVER IS RUNNING IN DEBUG MODE'.center(80), '*' * 80, sep='\n\n\n')


class _ErrorExclusionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return record.levelno < logging.ERROR


logging.config.dictConfig(dict(
    version=1,
    disable_existing_loggers=False,
    filters={
        'error_exclusion': {
            '()': _ErrorExclusionFilter,
        },
    },
    formatters={
        'standard': {
            'format': '%(levelname)-5s - [%(name)s:%(funcName)s]  %(message)s',
        }
    },
    handlers={
        'stdout': {
            'class': 'logging.StreamHandler',
            'filters': ['error_exclusion'],
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
        'stderr': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': logging.ERROR,
            'stream': 'ext://sys.stderr',
        },
    },
    loggers={
        'bfapi': {
            'handlers': ['stdout', 'stderr'],
            'level': logging.DEBUG if IS_DEBUG_MODE else logging.INFO,
        },
    }
))

log = logging.getLogger(__name__)
log.debug('Initialized logging')
