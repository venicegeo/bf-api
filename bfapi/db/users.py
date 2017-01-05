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

from datetime import datetime

from bfapi.db import Connection, ResultProxy

import uuid

def select_user(
        conn: Connection,
        *,
        geoaxis_uid: str) -> ResultProxy:
    query = """
        SELECT u.geoaxis_uid, u.user_name, u.api_key, u.created_on
          FROM __beachfront__user u
        WHERE u.geoaxis_uid = %(geoaxis_uid)s
        """
    params = {
        'geoaxis_uid': geoaxis_uid,
    }
    return conn.execute(query, params)

def select_user_by_api_key(
        conn: Connection,
        *,
        api_key: str) -> ResultProxy:
    query = """
        SELECT u.geoaxis_uid, u.user_name, u.api_key, u.created_on 
          FROM __beachfront__user u
         WHERE u.api_key = %(api_key)s
        """
    params = {
        'api_key': api_key,
    }
    return conn.execute(query, params)

def insert_or_update_user(
        conn: Connection,
        *,
        geoaxis_uid: str,
        user_name: str,
        api_key: str,
        should_force_api_key: bool) -> None:
    query = """
        INSERT INTO __beachfront__user (geoaxis_uid, user_name, api_key)
        VALUES (%(geoaxis_uid)s, %(user_name)s, %(api_key)s)
        ON CONFLICT (geoaxis_uid) DO UPDATE SET
            user_name = excluded.user_name
        """
    if should_force_api_key:
        query = query + """,
            api_key = excluded.api_key"""
    query = query + """
        """
    params = {
        'geoaxis_uid': geoaxis_uid,
        'user_name': user_name,
        'api_key': api_key,
    }
    conn.execute(query, params)