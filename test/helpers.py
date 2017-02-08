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

import io
import logging
import unittest.mock
from typing import List

import sqlalchemy.engine as _sqlalchemyengine
import sqlalchemy.exc as _sqlalchemyexc

import bfapi.db


def create_database_error():
    return _sqlalchemyexc.DatabaseError('test-query', None, Exception('test-error'))


def mock_database():
    mock = MockDBConnection()
    mock.install()
    return mock


def get_logger(name: str, fmt: str = '%(levelname)s - %(message)s'):
    wrapper = LoggerWrapper(name, fmt)
    wrapper.install()
    return wrapper


class LoggerWrapper:
    def __init__(self, name: str, fmt: str):
        self._stream = io.StringIO()
        self._logger = logging.getLogger(name)
        self._handler = logging.StreamHandler(self._stream)
        self._handler.setFormatter(logging.Formatter(fmt))

    def install(self):
        self._logger.handlers.clear()
        self._logger.addHandler(self._handler)

    def destroy(self):
        self._logger.handlers.clear()

    @property
    def lines(self) -> List[str]:
        return self._stream.getvalue().splitlines()


class MockDBConnection(unittest.mock.Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(spec=_sqlalchemyengine.Connection, *args, **kwargs)
        self._original_get_connection = None
        self._original_print_diagnostics = None
        self.transactions = []  # type: List[unittest.mock.Mock]

    def begin(self):
        transaction = unittest.mock.Mock(spec=_sqlalchemyengine.Transaction)
        self.transactions.append(transaction)
        return transaction

    def install(self):
        self._original_get_connection = bfapi.db.get_connection
        self._original_print_diagnostics = bfapi.db.print_diagnostics
        bfapi.db.get_connection = lambda: self
        bfapi.db.print_diagnostics = lambda _: None

    def destroy(self):
        if self._original_get_connection:
            bfapi.db.get_connection = self._original_get_connection
            bfapi.db.print_diagnostics = self._original_print_diagnostics

    @property
    def executed(self):
        return self.execute.called

    def raise_on_execute(self, err: _sqlalchemyexc.DatabaseError = None):
        if err is None:
            err = create_database_error()
        self.execute.side_effect = err
