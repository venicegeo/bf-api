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
import requests
import uuid

from datetime import datetime
from bfapi import db
from bfapi.config import GEOAXIS_ADDR

TIMEOUT = 24

# TO-DO:
#   ** add in audit logging
#   ** add in unit tests
#   ** somehow test the thing
#   if receiving auth token directly from ui:
#       build rest endpoint to receive it that calls geoaxis_token_login and returns user_name + api_key
#   else
#       build function to call geoaxis with oauth auth code and derive auth token
#       as above, except endpoint receives auth code
#   plug the user from this in with the user from the user/jobs connection

class User:
    def __init__(
            self,
            *,
            geoaxis_uid: str,
            user_name: str,
            bf_api_key: str = None,
            created_on: datetime = None ): 
        self.geoaxis_uid = geoaxis_uid
        self.user_name = user_name
        self.bf_api_key = bf_api_key
        self.created_on = created_on

def geoaxis_token_login(geo_auth_token: str) -> User:
    userprofile_addr = 'https://{}/ms_oauth/resources/userprofile/me'.format(GEOAXIS_ADDR)
    try:
        response = requests.get(
            userprofile_addr,
            timeout=TIMEOUT,
            headers={'Authorization': geo_auth_token},
        )
        response.raise_for_status()
        print(geo_auth_token, response)
    except requests.ConnectionError:
        raise CouldNotReachError(userprofile_addr)
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            raise UnauthorizedError(userprofile_addr)
        raise HttpCodeError(status_code, userprofile_addr)

    uid = response.json().get('uid')
    if not uid:
        raise ResponseError('missing `uid`', response.text, userprofile_addr)
    user_name = response.json().get('username')
    if not user_name:
        raise ResponseError('missing `username`', response.text, userprofile_addr)
    
    geoax_user = User(
        geoaxis_uid = uid,
        user_name = user_name,
    )
    return _db_harmonize(inp_user=geoax_user)

def new_api_key(geoaxis_uid: str) -> str:
    updated_user = _db_harmonize(User(geoaxis_uid=geoaxis_uid, bf_api_key = uuid.uuid4()))
    return updated_user.bf_api_key

def login_by_api_key(bf_api_key: str) -> User:
    conn = db.get_connection()
    try:
        row = db.user.select_user_by_api_key(conn, api_key=bf_api_key).fetchone()
    except db.DatabaseError as err:
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()
    if not row:
        return None
    if row['api_key'] != bf_api_key:
        err = DatabaseResultError("select_user_by_api_key", "api_key")
        db.print_diagnostics(err)
        raise err
    return User(
        geoaxis_uid=row['geoaxis_uid'],
        bf_api_key=row['api_key'],
        user_name=row['user_name'],
        created_on=row['created_on'],
    )

def get_by_id(geoaxis_uid: str) -> User:
    conn = db.get_connection()
    try:
        row = db.user.select_user(conn, geoaxis_uid=geoaxis_uid).fetchone()
    except db.DatabaseError as err:
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()
    if not row:
        return None
    if row['geoaxis_uid'] != geoaxis_uid:
        err = DatabaseResultError("select_user", "geoaxis_uid")
        db.print_diagnostics(err)
        raise err
    return User(
        geoaxis_uid=row['geoaxis_uid'],
        bf_api_key=row['api_key'],
        user_name=row['user_name'],
        created_on=row['created_on'],
    )

def _db_harmonize(inp_user: User) -> User:
    log = logging.getLogger(__name__)
    if inp_user is None:
        raise Exception("_db_harmonize called on empty User object")
    db_user = get_by_id(inp_user.geoaxis_uid)
    if db_user is None:
        if not inp_user.bf_api_key:
            inp_user.bf_api_key = uuid.uuid4()
            
        conn = db.get_connection()
        transaction = conn.begin()
        try:
            db.user.insert_user(
                conn,
                geoaxis_uid=inp_user.geoaxis_uid,
                user_name=inp_user.user_name,
                api_key=inp_user.bf_api_key,
            )
            transaction.commit()
        except db.DatabaseError as err:
            transaction.rollback()
            log.error('Could not save user to database: %s', err)
            db.print_diagnostics(err)
            raise
        finally:
            conn.close()
        return inp_user
    else:
        if inp_user.user_name != "":
            db_user.user_name = inp_user.user_name
        if inp_user.bf_api_key:
            db_user.bf_api_key = inp_user.bf_api_key
        conn = db.get_connection()
        transaction = conn.begin()
        try:
            db.user.update_user(
                conn,
                geoaxis_uid=inp_user.geoaxis_uid,
                user_name=inp_user.user_name,
                api_key=inp_user.bf_api_key,
            )
            transaction.commit()
        except db.DatabaseError as err:
            transaction.rollback()
            log.error('Could not update user %s in database: %s', inp_user.geoaxis_uid, err)
            db.print_diagnostics(err)
            raise
        finally:
            conn.close()
        return db_user

# Note: BMB: This shoudl probably be integrated with the Error objects currently in service/jobs.py,
# but if we do that, it probably shouldn't be in jobs.py.  I wasnt' sure where to put it, and
# I wasn't confident about refactoring things that weren't my stuff unnecessarily.

#
# Errors
#


class Error(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class DatabaseResultError(Error):
    def __init__(self, func_name: str, db_entry: str):
        super().__init__("Database result error: {} returned entry with incorrect {}.".format(func_name, db_entry))

class CouldNotReachError(Error):
    def __init__(self, targ_addr: str):
        super().__init__('{} is unreachable'.format(targ_addr))

class UnauthorizedError(Error):
    def __init__(self, targ_addr: str):
        super().__init__('Not authorized to access {}'.format(targ_addr))

class HttpCodeError(Error):
    def __init__(self, status_code: int, targ_addr: str):
        super().__init__('Http Code error (HTTP {}) at {}'.format(status_code, targ_addr))
        self.status_code = status_code

class ResponseError(Error):
    def __init__(self, message: str, response_text: str, targ_addr: str):
        super().__init__('invalid http response from {}: ' + message)
        self.response_text = response_text
