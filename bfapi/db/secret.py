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
import datetime

def find_and_mark_one_time_key_used(
        conn: Connection,
        key: str) -> bool:
    query = """
        Update __beachfront__secret
        Set used_on=%(datetime)s
        WHERE key = %(key)s
        """
    params = {
        'datetime' : datetime.datetime.now(),
        'key': key,
    }
    return conn.execute(query, params).rowcount > 0


def check_if_one_time_key_exists(
        conn: Connection,
        key: str) -> bool:
    query = """
        SELECT key FROM __beachfront__secret WHERE key = %(key)s and used_on is null
        """
    params = {
        'key': key,
    }
    return conn.execute(query, params).rowcount > 0

def insert_one_time_key(
        conn: Connection,
        key: str) -> None:
    query = """
        INSERT INTO __beachfront__secret (key,used_on) values ( %(key)s , null )
        """
    params = {
        'key': key,
    }
    conn.execute(query, params)