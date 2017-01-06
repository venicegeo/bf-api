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
from bfapi.db import secret

"""Used to set the single use key"""
def setSingleUseKey( uuid ):
    conn = db.get_connection()
    try:
        secret.insert_key(conn,uuid)
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
        if secret.exists(conn,string):
            try:
                key = secret.used_key(conn,string)
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
def decrypt( str ):
    secret = os.getenv('JWT_SECRET')
    try:
        payload= jwt.decode(str,secret)
    except jwt.ExpiredSignature:
        return handle_error({'code': 'token_expired', 'description': 'token is expired'}, 401)
    except jwt.InvalidAudienceError:
        return handle_error({'code': 'invalid_audience', 'description': 'incorrect audience, expected: ' + clientID}, 401)
    except jwt.DecodeError:
        return handle_error({'code': 'token_invalid_signature', 'description': 'token signature is invalid'}, 401)
    except Exception:
        return handle_error({'code': 'invalid_header', 'description':'Unable to create authentication token.'}, 400)
    if payload['JWT_OTU']=='none':       
        return payload
    else:
        testBool = getSingleUseKey(payload['JWT_OTU'])
        print(testBool)
        if testBool:
            return payload
        else:
            return "Single Use Token Used"


"""Encrypts payload and returns JWT"""
def encrypt( payload ):
    secret = os.getenv('JWT_SECRET')
    if secret=="":
        return "Secret has no value"
    elif payload=="":
        return "Payload has no value"
    else:
        try:
            if payload['JWT_OTU'].lower()=="yes":
                key=str(uuid.uuid4())
                setSingleUseKey(key)
                payload['JWT_OTU'] = key
            else:
                payload['JWT_OTU'] = 'none'
            jwtString= jwt.encode(
                payload,
                secret
                )
        except Exception:
            return handle_error({'code': 'invalid_header', 'description':'Unable to parse authentication token.'}, 400)
    return jwtString
        
