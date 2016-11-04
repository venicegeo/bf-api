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

import unittest.mock

import sqlalchemy.engine as _sqlalchemyengine
import sqlalchemy.exc as _sqlalchemyexc

import bfapi.db


def mock_database():
    mock = MockDBConnection()
    mock.install()
    return mock


class MockDBConnection(unittest.mock.Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(spec=_sqlalchemyengine.Connection, *args, **kwargs)
        self._original_get_connection = None

    #
    # Lifecycle
    #

    def install(self):
        self._original_get_connection = bfapi.db.get_connection
        bfapi.db.get_connection = lambda: self

    def destroy(self):
        if self._original_get_connection:
            bfapi.db.get_connection = self._original_get_connection

    #
    # Assertion Helpers
    #

    @property
    def executed(self):
        return self.execute.called

    def raise_on_execute(self, err: _sqlalchemyexc.DatabaseError = None):
        if err is None:
            err = _sqlalchemyexc.DatabaseError('test-query', None, Exception('test-error'))
        self.execute.side_effect = err
