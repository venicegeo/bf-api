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

import sqlalchemy as sa
import sqlalchemy.exc as sae
from sqlalchemy.engine import Engine, Connection, ResultProxy as Cursor

from bfapi.config import POSTGRES_DATABASE, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USERNAME

CONNECTION_TIMEOUT = 15

_engine = None  # type: Engine


def cleanup():
    global _engine
    log = logging.getLogger(__name__)
    log.info('Closing database connection')
    _engine.dispose()
    _engine = None
    log.info('Done')


def get_connection() -> Connection:
    log = logging.getLogger(__name__)
    try:
        return _engine.connect()
    except sae.OperationalError as err:
        log.critical('Database connection failed: %s', err)
        raise ConnectionFailed(err)


def init():
    log = logging.getLogger(__name__)
    global _engine
    try:
        _engine = sa.create_engine(
            'postgresql://{user}:{password}@{host}:{port}/{database}'.format(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USERNAME,
                database=POSTGRES_DATABASE,
                password=POSTGRES_PASSWORD,
            ))
        _install_if_needed()
    except:
        log.exception('Initialization failed', exc_info=True)
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


#
# Helpers
#

def _install():
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
    try:
        _engine.execute(sa.text(schema_query))
    except sae.DatabaseError as err:
        log.critical('Installation failed: %s', err)
        err = DatabaseError(err)
        err.print_diagnostics()
        raise InstallationError('schema install failed', err)

    log.info('Installation complete!')


def _install_if_needed():
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
    try:
        is_installed, = _engine.execute(sa.text(query)).fetchone()
    except sae.DatabaseError as err:
        log.critical('Could not test for : %s', err)
        err = DatabaseError(err)
        err.print_diagnostics()
        log.critical('Schema verification failed: %s', err)
        raise InstallationError('schema execution failed', err)

    if is_installed:
        log.info('Schema exists and will not be reinstalled')
        return

    _install()


def _read_sql_file(name: str) -> str:
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    with open(os.path.join(root_dir, 'sql', name)) as fp:
        return fp.read()


#
# Errors
#

class ConnectionFailed(Exception):
    def __init__(self, err: sae.DatabaseError, message: str = 'cannot connect to database'):
        super().__init__(message)
        self.original_error = err


class DatabaseError(Exception):
    def __init__(self, err: sae.StatementError):
        super().__init__('database error: {}'.format(err))
        self.original_error = err

    def print_diagnostics(self):
        print(
            '!' * 80,
            '',
            'DatabaseError: {}'.format(self.original_error),
            '',
            'QUERY',
            self.original_error.statement.rstrip(),
            '',
            'PARAMS',
            '',
            pprint.pformat(self.original_error.params, indent=4),
            '!' * 80,
            sep='\n'
        )


class InstallationError(Exception):
    def __init__(self, message: str, err: Exception = None):
        super().__init__(message)
        self.original_error = err
