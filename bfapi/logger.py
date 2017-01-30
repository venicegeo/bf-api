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

import os
import logging.config

import sys

ACTOR_SYSTEM = 'SYSTEM'
APP_NAME     = 'beachfront'
DATE_FORMAT  = '%Y-%d-%mT%H:%M:%SZ'
FACILITY     = 1
FORMAT       = ('<{PRI}>1 {asctime} {HOSTNAME} {APP_NAME} {name}:{funcName} '
                '[{SD_ID} actor="{ACTOR}" action="{ACTION}" actee="{ACTEE}"] {levelname:<5} {message}')
HOSTNAME     = os.uname()[1].lower()
SD_ID        = 'bfaudit@48851'

PRI_CODES = {
    'FATAL':    0,
    'CRITICAL': 2,
    'ERROR':    3,
    'WARN':     4,
    'WARNING':  4,
    'NOTICE':   5,
    'INFO':     6,
    'DEBUG':    7,
}


def init(debug: bool = False):
    logging.basicConfig(
        datefmt=DATE_FORMAT,
        format=FORMAT,
        level=logging.DEBUG if debug else logging.INFO,
        stream=sys.stdout,
        style='{',
    )
    logging.setLoggerClass(AuditableLogger)
    log = logging.getLogger(__name__)
    log.debug('Initialized')


#
# Helpers
#

class AuditableLogger(logging.Logger):
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False,
             actee='', action='', actor='', **kwargs):

        # Assemble RFC 5424 elements
        facility = FACILITY << 3
        pri_code = facility | PRI_CODES.get(logging.getLevelName(level), PRI_CODES['NOTICE'])
        hostname = os.uname()[1].lower()
        extra = {
            'ACTEE':     actee,
            'ACTION':    action,
            'ACTOR':     actor or ACTOR_SYSTEM,
            'APP_NAME':  APP_NAME,
            'HOSTNAME':  hostname,
            'PRI':       pri_code,
            'SD_ID':     SD_ID,
        }

        super()._log(level, msg, args, exc_info, extra, stack_info)
