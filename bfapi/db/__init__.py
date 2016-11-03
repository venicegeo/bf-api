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
import os.path
import pprint
import signal

import psycopg2 as pg
from psycopg2.extras import DictCursor as CursorFactory
from psycopg2.psycopg1 import connection as Connection, cursor as Cursor

from bfapi.config import POSTGRES_DATABASE, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USERNAME

CONNECTION_TIMEOUT = 15

_conn = None  # type: Connection

def get_connection() -> Connection:
    global _conn
    log = logging.getLogger(__name__)
    try:
        if not _conn or _conn.closed:
            log.debug('Connecting to database <{}:{}/{}>'.format(POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE))
            _conn = pg.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USERNAME,
                database=POSTGRES_DATABASE,
                password=POSTGRES_PASSWORD,
                connect_timeout=CONNECTION_TIMEOUT,
                cursor_factory=pge.DictCursor,
            )
        else:
            log.debug('Reusing open connection to database <{}:{}/{}>'.format(POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE))
        return _conn
    except pg.OperationalError as err:
        log.critical('Database connection failed: %s', err)
        raise ConnectionFailed(err)


def init():
    try:
        install_if_needed()
    except:
        # Fail fast
        print(
            '-' * 80,
            'Halting server initialization.'.center(80),
            '-' * 80,
            sep='\n\n',
        )
        os.kill(os.getppid(), signal.SIGQUIT)
        signal.pause()
        exit(1)


def install():
    conn = get_connection()
    log = logging.getLogger(__name__)

    log.info('Installing schema')

    # Load SQL script
    try:
        schema_query = _read_sql_file('schema.install.sql')
    except Exception as err:
        err = InstallationError('cannot open schema.install.sql', err)
        log.critical('Installation failed: %s', err)
        raise err

    # Execute
    cursor = conn.cursor()  # type: Cursor
    try:
        cursor.execute(schema_query)
    except pg.Error as err:
        log.critical('Installation failed: %s', err)
        conn.rollback()
        err = DatabaseError(err, schema_query)
        err.print_diagnostics()
        raise InstallationError('schema install failed', err)

    conn.commit()
    log.info('Installation complete!')


def install_if_needed():
    conn = get_connection()
    log = logging.getLogger(__name__)

    log.info('Checking to see if installation is required')

    # Load SQL script
    try:
        query = _read_sql_file('schema.exists.sql')
    except Exception as err:
        err = InstallationError('cannot open schema.exists.sql', err)
        log.critical('Schema verification failed: %s', err)
        raise err

    # Execute
    cursor = conn.cursor()  # type: Cursor
    try:
        cursor.execute(query)
        is_installed, = cursor.fetchone()
    except pg.Error as err:
        log.critical('Could not test for : %s', err)
        err = DatabaseError(err, query)
        err.print_diagnostics()
        log.critical('Schema verification failed: %s', err)
        raise InstallationError('schema execution failed', err)

    if is_installed:
        log.info('Schema exists and will not be reinstalled')
        return

    install()


#
# Helpers
#

def _read_sql_file(name: str) -> str:
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    with open(os.path.join(root_dir, 'sql', name)) as fp:
        return fp.read()


#
# Errors
#

class ConnectionFailed(Exception):
    def __init__(self, err: pg.Error, message: str = 'cannot connect to database'):
        super().__init__(message)
        self.original_error = err


class DatabaseError(Exception):
    def __init__(self, err: pg.Error, query: str, params: dict = None):
        super().__init__('database error: {}'.format(err))
        self.original_error = err
        self.query = query
        self.params = params

    def print_diagnostics(self):
        print(
            '!' * 80,
            '',
            'DatabaseError: {}'.format(self.original_error),
            '',
            'QUERY',
            self.query.rstrip(),
            '',
            'PARAMS',
            '',
            pprint.pformat(self.params, indent=4),
            '!' * 80,
            sep='\n'
        )


class InstallationError(Exception):
    def __init__(self, message: str, err: Exception = None):
        super().__init__(message)
        self.original_error = err
