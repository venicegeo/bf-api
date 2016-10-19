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

from os.path import dirname, join
from pprint import pprint
import sqlite3

from bfapi.logger import get_logger


def get_connection() -> sqlite3.Connection:
    log = get_logger()
    filepath = join(dirname(dirname(dirname(__file__))), 'temporary.db')
    log.debug('Connecting to database: {}'.format(filepath))
    conn = sqlite3.connect(filepath)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


#
# Errors
#

class DatabaseError(Exception):
    def __init__(self, err: sqlite3.Error, query: str, params: dict = None):
        super().__init__('Database error: {}'.format(err))
        self.original_error = err
        self.query = query
        self.params = params

    def print_diagnostics(self):
        print('!' * 80)
        print()
        print('DatabaseError: {}'.format(self.original_error))
        print()
        print('QUERY')
        print(self.query.rstrip())
        print()
        print('PARAMS')
        print()
        pprint(self.params, indent=4)
        print()
        print('!' * 80)
