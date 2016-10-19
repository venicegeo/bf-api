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
from logging import Formatter, StreamHandler, Logger, DEBUG, INFO

from flask import Flask

_app = None
_module_root = dirname(__file__)


#
# Actions
#

def init(app: Flask):
    global _app
    _app = app

    _app.logger.handlers.clear()  # TODO -- is this legit?

    handler = StreamHandler(stream=sys.stdout)
    formatter = CustomFormatter('[%(relativePathname)s:%(funcName)s] %(levelname)5s - %(message)s')
    handler.setFormatter(formatter)
    # handler.setLevel(DEBUG if _app.debug else INFO)
    handler.setLevel(INFO)

    _app.logger.addHandler(handler)


def get_logger() -> Logger:
    return _app.logger


#
# Types
#

class CustomFormatter(Formatter):
    def formatMessage(self, record):
        record.relativePathname = relpath(record.pathname, _module_root)
        return super().formatMessage(record)
