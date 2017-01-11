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

import jwt
import os
import string
import random
import uuid
import json

from bfapi import db
from bfapi.config import SESSION_SECRET
from bfapi.db import secret


"""Used to set the single use key"""
def setSingleUseKey( uuid ):
    conn = db.get_connection()
    try:
        secret.insert_one_time_key(conn,uuid)
    except db.DatabaseError as err:
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()
    return

"""Used to find single use key and mark it as used"""
def getSingleUseKey( string ):
    try:
        conn = db.get_connection()
        if secret.check_if_one_time_key_exists(conn,string):
            try:
                key = secret.find_and_mark_one_time_key_used(conn,string)
            except db.DatabaseError as err:
                db.print_diagnostics(err)
                raise
            finally:
                conn.close()
            return True
        else:
            return False
    except db.DatabaseError as err:
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()

"""Decrypts JWT and returns payload the boolean will check if its a single use key"""
def decrypt( token ):
    try:
        payload= jwt.decode(token,SESSION_SECRET)
    except jwt.ExpiredSignature:
        raise DecryptError('token expired')
    except jwt.DecodeError:
        raise DecryptError('invalid signiture')
    except Exception:
        raise DecryptError('invalid header')
    one_time_use_token= payload.get('JWT_OTU')
    if not one_time_use_token:       
        return payload
    else:
        resultBool = getSingleUseKey(one_time_use_token)
        if resultBool:
            return payload
        else:
            raise DecryptError('one time use token expired')


"""Encrypts payload and returns JWT"""
def encrypt( payload ):
    try:
        if not payload.get('JWT_OTU'):
            payload['JWT_OTU'] = None
        else:
            key=str(uuid.uuid4())
            setSingleUseKey(key)
            payload['JWT_OTU'] = key
        jwtString= jwt.encode(
            payload,
            SESSION_SECRET
            )
    except Exception:
        raise EncryptError('unable to decrypt')
    return jwtString

class Error(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class DecryptError(Error):
    def __init__(self, message: str):
        super().__init__('Cannot Decrypt: {}'.format(message))

class EncryptError(Error):
    def __init__(self, message: str):
        super().__init__('Cannot Decrypt: {}'.format(message))


