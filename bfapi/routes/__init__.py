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

import time
import urllib.parse

import flask

from bfapi.config import DOMAIN, UI, GEOAXIS, GEOAXIS_CLIENT_ID
from bfapi.service import users
from bfapi.routes import v0

_time_started = time.time()


def health_check():
    uptime = round(time.time() - _time_started, 3)
    return flask.jsonify({
        'uptime': uptime,
    })



def is_login_active():
    """This should be mounted behind the verification middleware"""
    return '', 204

#Audit Log Required: Login
def login():
    query_params = flask.request.args
    log = logging.getLogger(__name__)
    auth_code = query_params.get('code', '').strip()
    if not auth_code:      
        log.info('Login Failed', extra={'actor': 'system', 'actee': 'system', 'action': 'Cannot log in: invalid "code" query parameter'})
        return 'Cannot log in: invalid "code" query parameter', 400
    try:
        log.info('Attempting Login', extra={'actor': 'system', 'actee': 'system', 'action': 'login attempt'})
        user = users.authenticate_via_geoaxis(auth_code)
    except users.Unauthorized as err:
        log.info('Login Failed', extra={'actor': 'system', 'actee': 'system', 'action': 'unauthorised user'})
        return str(err), 401
    except users.GeoaxisUnreachable as err:
        log.info('Login Failed', extra={'actor': 'system', 'actee': 'system', 'action': 'Geoaxis unreachable'})
        return str(err), 503
    except users.Error:
        log.info('Login Failed', extra={'actor': 'system', 'actee': 'system', 'action': 'internal error'})
        return 'Cannot log in: an internal error prevents authentication', 500

    flask.session.permanent = True
    flask.session['api_key'] = user.api_key

    # Send user back to the UI
    return flask.redirect('https://{}?logged_in=true'.format(UI))


def login_start():
    """
    Avoid having to drop GeoAxis configuration into bf-ui
    """
    params = urllib.parse.urlencode((
        ('client_id', GEOAXIS_CLIENT_ID),
        ('redirect_uri', 'https://bf-api.{}/login'.format(DOMAIN)),
        ('response_type', 'code'),
        ('scope', 'UserProfile.me'),
    ))
    return flask.redirect('https://{}/ms_oauth/oauth2/endpoints/oauthservice/authorize?{}'.format(GEOAXIS, params))


def logout():
    flask.session.clear()
    log = logging.getLogger(__name__)
    log.info('Attempting logout', extra={'actor': 'system', 'actee': 'system', 'action': 'user logout'})
    return 'You have been logged out'
