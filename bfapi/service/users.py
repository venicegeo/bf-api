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
from bfapi.config import GEOAXIS

TIMEOUT = 24

# TO-DO:
#   add in audit logging
#   if receiving auth token directly from ui:
#       build rest endpoint to receive auth token from ui, then calls geoaxis_token_login and returns user_name + api_key
#   else
#       build function to call geoaxis with oauth auth code and derive auth token
#       build rest endpoint to receive auth code from ui, then calls the above, then calls geoaxis_token_login and returns
#   plug the user from this in with the user from the user/jobs connection

class User:
    def __init__(
            self,
            *,
            user_id: str,
            user_name: str,
            bf_api_key: str = None,
            created_on: datetime = None ): 
        self.user_id = user_id
        self.user_name = user_name
        self.bf_api_key = bf_api_key
        self.created_on = created_on

def authenticate_via_geoaxis(geoaxis_token: str) -> User:
    userprofile_addr = 'https://{}/ms_oauth/resources/userprofile/me'.format(GEOAXIS)
    log = logging.getLogger(__name__)
    try:
        response = requests.get(
            userprofile_addr,
            timeout=TIMEOUT,
            headers={'Authorization': geoaxis_token},
        )
        response.raise_for_status()
        log.debug(geoaxis_token, response)
    except requests.ConnectionError:
        log.error('Could not reach GeoAxis')
        raise GeoaxisUnreachable()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            raise GeoaxisUnauthorized()
        raise GeoaxisError(status_code)

    jsonOut = response.json()
    user_id = jsonOut.get('uid')
    if not user_id:
        log.error('Geoaxis responded to userprofile call without uid.  Response Text: '.format(response.text))
        raise InvalidGeoaxisResponse('missing `uid`', response.text)
    user_name = jsonOut.get('username')
    if not user_name:
        log.error('Geoaxis responded to userprofile call without user name.  Response Text: '.format(response.text))
        raise InvalidGeoaxisResponse('missing `username`', response.text)
    
    conn = db.get_connection()
    try:
        db.users.insert_or_update_user(
            conn,
            user_id=user_id,
            user_name=user_name,
            api_key=str(uuid.uuid4()),
            should_force_api_key=False
        )
    except db.DatabaseError as err:
        log.error('Could not insert/update user to database: %s', err)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()
    return get_by_id(user_id)

def authenticate_via_api_key(api_key: str) -> User:
    log = logging.getLogger(__name__)
    conn = db.get_connection()
    try:
        row = db.users.select_user_by_api_key(conn, api_key=api_key).fetchone()
    except db.DatabaseError as err:
        log.error("Attempt to find user by api key failed in database: %s", err)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()
    if not row:
        raise BeachfrontUnauthorized()
    if row['api_key'] != api_key:
        err = DatabaseMismatchError("select_user_by_api_key", "api_key")
        log.error('Database returned wrong information: %s', err)
        raise err
    return User(
        user_id=row['user_id'],
        bf_api_key=row['api_key'],
        user_name=row['user_name'],
        created_on=row['created_on'],
    )

def get_by_id(user_id: str) -> User:
    log = logging.getLogger(__name__)
    conn = db.get_connection()
    try:
        row = db.users.select_user(conn, user_id=user_id).fetchone()
    except db.DatabaseError as err:
        log.error("Attempt to find user by user_id failed in database: %s", err)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()
    if not row:
        return None
    if row['user_id'] != user_id:
        err = DatabaseMismatchError("select_user", "user_id")
        log.error('Database returned wrong information: %s', err)
        raise err
    return User(
        user_id=row['user_id'],
        bf_api_key=row['api_key'],
        user_name=row['user_name'],
        created_on=row['created_on'],
    )

#
# Errors
#

class Error(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class BeachfrontUnauthorized(Error):
    def __init__(self):
        super().__init__('Beachfront authorization rejected.')

class DatabaseMismatchError(Error):
    def __init__(self, func_name: str, db_entry: str):
        super().__init__("Database mismatch error: {} returned entry with incorrect {}.".format(func_name, db_entry))

class GeoaxisUnreachable(Error):
    def __init__(self):
        super().__init__('Geoaxis is unreachable')

class GeoaxisUnauthorized(Error):
    def __init__(self):
        super().__init__('GeoAxis rejected your authorization')

class GeoaxisError(Error):
    def __init__(self, status_code: int):
        super().__init__('Call to GeoAxis generated Http Code {}'.format(status_code))
        self.status_code = status_code

class InvalidGeoaxisResponse(Error):
    def __init__(self, message: str, response_text: str):
        super().__init__('Invalid Http response from GeoAxis: ' + message)
        self.response_text = response_text
