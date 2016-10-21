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

from os.path import dirname, relpath
import sys
from logging import Formatter, NullHandler, StreamHandler, Logger, DEBUG, INFO

_MODULE_ROOT = dirname(__file__)

_logger = None


#
# Actions
#

def init(debug_mode: bool = False):
    global _logger

    if debug_mode:
        print('*' * 80, '\u26A0 ️SERVER IS RUNNING IN DEBUG MODE'.center(80), '*' * 80, sep='\n\n\n')

    _logger = Logger('bfapi', level=DEBUG if debug_mode else INFO)
    handler = StreamHandler(stream=sys.stdout)
    formatter = CustomFormatter('%(levelname)-5s - [%(relativePathname)s:%(funcName)s]  %(message)s')
    handler.setFormatter(formatter)

    _logger.addHandler(handler)


def get_logger() -> Logger:
    if not _logger:
        nil = Logger('bfapi-nil')
        nil.handlers.clear()
        nil.addHandler(NullHandler())
        return nil
    return _logger


#
# Types
#

class CustomFormatter(Formatter):
    def formatMessage(self, record):
        record.relativePathname = relpath(record.pathname, _MODULE_ROOT)
        return super().formatMessage(record)
