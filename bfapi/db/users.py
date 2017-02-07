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

from bfapi.db import Connection, ResultProxy
import logging

def select_user(
        conn: Connection,
        *,
        user_id: str) -> ResultProxy:
    log = logging.getLogger(__name__)
    log.info('Db select user', action='database query record')
    query = """
        SELECT u.user_id, u.user_name, u.api_key, u.created_on
          FROM __beachfront__user u
        WHERE u.user_id = %(user_id)s
        """
    params = {
        'user_id': user_id,
    }
    return conn.execute(query, params)


def select_user_by_api_key(
        conn: Connection,
        *,
        api_key: str) -> ResultProxy:
    log = logging.getLogger(__name__)
    log.info('Db select user by api', action='database query record')
    query = """
        SELECT u.user_id, u.user_name, u.api_key, u.created_on
          FROM __beachfront__user u
         WHERE u.api_key = %(api_key)s
        """
    params = {
        'api_key': api_key,
    }
    return conn.execute(query, params)


def insert_user(
        conn: Connection,
        *,
        user_id: str,
        user_name: str,
        api_key: str) -> None:
    log = logging.getLogger(__name__)
    log.info('Db insert user', action='database insert record')
    query = """
        INSERT INTO __beachfront__user (user_id, user_name, api_key)
        VALUES (%(user_id)s, %(user_name)s, %(api_key)s)
        """
    params = {
        'user_id': user_id,
        'user_name': user_name,
        'api_key': api_key,
    }
    conn.execute(query, params)
