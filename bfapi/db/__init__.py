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

from logging import getLogger
from os.path import dirname, join
import sqlite3


def get_connection() -> sqlite3.Connection:
    log = getLogger(__name__)
    filepath = join(dirname(dirname(dirname(__file__))), 'temporary.db')
    log.debug('Connecting to database: {}'.format(filepath))
    conn = sqlite3.connect(filepath)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


class DatabaseError(Exception):
    def __init__(self, err: sqlite3.OperationalError, message=None):
        if not message:
            (message,) = err.args
        super.__init__(message)
        self.message = message
        self.original_error = err

    def __str__(self):
        return 'DatabaseError: {}'.format(self.message)
