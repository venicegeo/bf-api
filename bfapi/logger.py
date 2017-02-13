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

import datetime
import os
import logging.config
import sys


APP_NAME     = 'beachfront'
FACILITY     = 1
FORMAT       = ('<{PRI}>1 {TIMESTAMP} {HOSTNAME} {APP_NAME} {process} {MSG_ID}'
                ' {SD_ELEMENT}'
                '({name}:{funcName}) {levelname:<5} {message}')
HOSTNAME     = os.uname()[1].lower()
MSG_ID       = '-'
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


def init(*, debug: bool, muted: bool):
    logging.basicConfig(
        format=FORMAT,
        level=logging.DEBUG if debug else logging.INFO,
        stream=sys.stdout,
        style='{',
    )
    logging.setLoggerClass(AuditableLogger)

    # Prevent spamming test outputs
    if muted:
        logging.root.handlers = [logging.NullHandler()]

    log = logging.getLogger(__name__)
    log.debug('Initialized')


#
# Helpers
#

class AuditableLogger(logging.Logger):
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False,
             actee='', action='', actor='', **kwargs):
        sd_params = []
        if actor:
            sd_params.append('actor="{}"'.format(actor))
        if action:
            sd_params.append('action="{}"'.format(action))
        if actee:
            sd_params.append('actee="{}"'.format(actee))

        sd_element = ''
        if sd_params:
            sd_element = '[{SD_ID} {SD_PARAMS}] '.format(
                SD_ID=SD_ID,
                SD_PARAMS=' '.join(sd_params),
            )

        # Assemble RFC 5424 elements
        extra = {
            'ACTEE':     actee,
            'ACTION':    action,
            'ACTOR':     actor,
            'APP_NAME':  APP_NAME,
            'HOSTNAME':  HOSTNAME,
            'MSG_ID':    MSG_ID,
            'PRI':       (FACILITY << 3) | PRI_CODES.get(logging.getLevelName(level),
                                                         PRI_CODES['NOTICE']),
            'SD_ELEMENT': sd_element,
            'TIMESTAMP': datetime.datetime.utcnow().isoformat() + 'Z',
        }

        super()._log(level, msg, args, exc_info, extra, stack_info)
