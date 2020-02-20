'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

import requests
import base64
import time
from contextlib import closing

from app.utils_file_loads import get_unity
from app.utils_hub_update import token
from app.utils_common import remove_secret, SpawnException
from app.utils_db import set_skip
import json


def renew_token(app_logger, uuidcode, token_url, authorize_url, refreshtoken, accesstoken, expire, jhubtoken, app_hub_url_proxy_route, app_hub_token_url, username, servername, app_database):
    try:
        if int(expire) - time.time() > 480:
            return accesstoken, expire
    except:
        app_logger.warning("uuidcode={} - Could not check if token will expire soon. Try to renew token.".format(uuidcode))
    app_logger.info("uuidcode={} - Renew Token".format(uuidcode))
    unity = get_unity()
    if token_url == '':
        app_logger.warning("uuidcode={} - Use default token_url. Please send token_url in header".format(uuidcode))
        token_url = unity.get('links').get('token')
    tokeninfo_url = unity[token_url].get('links', {}).get('tokeninfo')
    cert_path = unity[token_url].get('certificate', False)
    scope = ' '.join(unity[authorize_url].get('scope'))
    b64key = base64.b64encode(bytes('{}:{}'.format(unity[token_url].get('client_id'), unity[token_url].get('client_secret')), 'utf-8')).decode('utf-8')
    data = {'refresh_token': refreshtoken,
            'grant_type': 'refresh_token',
            'scope': scope}
    headers = {'Authorization': 'Basic {}'.format(b64key),
               'Accept': 'application/json'}
    changed_skip = False
    try:
        for i in range(0,10):
            try:
                app_logger.info("uuidcode={} - Post to {}".format(uuidcode, token_url))
                app_logger.trace("uuidcode={} - Header: {}".format(uuidcode, headers))
                app_logger.trace("uuidcode={} - Data: {}".format(uuidcode, data))
                with closing(requests.post(token_url,
                                           headers = headers,
                                           data = data,
                                           verify = cert_path,
                                           timeout = 1800)) as r:
                    app_logger.trace("uuidcode={} - Unity Response: {} {} {} {}".format(uuidcode, r.text, r.status_code, r.headers, r.json))
                    if r.status_code == 400:
                        # wrong refresh_token, send cancel
                        error_msg = "Unknown Error. An Administrator is informed."
                        try:
                            r_json = json.loads(r.text)
                            if r_json.get('error_description', '') != "Invalid request; wrong refresh token":
                                app_logger.error("uuidcode={} - Received unknown answer from Unity: {}".format(uuidcode, r.text))
                            else:
                                error_msg = "Invalid token. Please logout and login again."
                        except:
                            try:
                                app_logger.exception("uuidcode={} - Could not check for Unity error description: {}".format(uuidcode, r.text))
                            except:
                                app_logger.exception("uuidcode={} - Could not check for Unity error description".format(uuidcode))
                        raise SpawnException(error_msg)
                    accesstoken = r.json().get('access_token')
                app_logger.info("uuidcode={} - Get to {}".format(uuidcode, tokeninfo_url))
                with closing(requests.get(tokeninfo_url,
                                          headers = { 'Authorization': 'Bearer {}'.format(accesstoken) },
                                          verify = cert_path,
                                          timeout = 1800)) as r:
                    app_logger.trace("uuidcode={} - Unity Response: {} {} {} {}".format(uuidcode, r.text, r.status_code, r.headers, r.json))
                    expire = r.json().get('exp')
                    break
            except:
                app_logger.warning("uuidcode={} - Could not update token. This was the {}/10 try. {}".format(uuidcode, i+1, "Raise Exception" if i==9 else "Try again in 30 seconds"))
                if i==0:
                    app_logger.warning("uuidcode={} - Set Skip to True for userserver={}".format(uuidcode, servername))
                    set_skip(app_logger,
                             uuidcode,
                             servername,
                             app_database,
                             'True')
                    changed_skip = True
                if i==9:
                    raise Exception("uuidcode={} - Tried 10 times".format(uuidcode))
                time.sleep(30)
    except:
        app_logger.warning("uuidcode={} - Could not update token".format(uuidcode))
        raise Exception("uuidcode={} - Could not update token".format(uuidcode))
    if changed_skip:
        app_logger.warning("uuidcode={} - Set Skip to False for userserver={}".format(uuidcode, servername))
        set_skip(app_logger,
                 uuidcode,
                 servername,
                 app_database,
                 'False')
    app_logger.debug("uuidcode={} - Token renewed".format(uuidcode))
    token(app_logger,
          uuidcode,
          app_hub_url_proxy_route,
          app_hub_token_url,
          jhubtoken,
          accesstoken,
          expire,
          username,
          servername)
    return accesstoken, expire

def communicate(app_logger, uuidcode, method, method_args, success_code=200):
    app_logger.trace("uuidcode={} - Start unity.communicate()".format(uuidcode))
    app_logger.trace("uuidcode={} - Method: {} - Method_args: {}".format(uuidcode, method, method_args))
    if method == "POST":
        try:
            app_logger.info("uuidcode={} - Post to {}".format(uuidcode, method_args.get('url', '<no_url>')))
            with closing(requests.post(method_args['url'],
                                       headers = method_args.get('headers', {}),
                                       data = method_args.get('data', "{}"),
                                       verify = method_args.get('certificate', False),
                                       timeout = 1800)) as r:
                if r.status_code != success_code:
                    app_logger.warning("uuidcode={} - Unity communication response: {} {}".format(uuidcode, r.text, r.status_code))
                    app_logger.warning("uuidcode={} - arguments: method_args: {}".format(uuidcode, remove_secret(method_args)))
                else:
                    app_logger.trace("uuidcode={} - Unity call successful".format(uuidcode))
        except:
            app_logger.exception("uuidcode={} - Unity communication failed".format(uuidcode))
    if method == "GET":
        try:
            app_logger.info("uuidcode={} - Get to {}".format(uuidcode, method_args.get('url', '<no_url>')))
            with closing(requests.get(method_args['url'],
                                      headers = method_args.get('headers', {}),
                                      verify = method_args.get('certificate', False),
                                      timeout = 1800)) as r:
                if r.status_code != success_code:
                    app_logger.warning("uuidcode={} - Unity communication response: {} {}".format(uuidcode, r.text, r.status_code))
                    app_logger.warning("uuidcode={} - arguments: method_args: {}".format(uuidcode, remove_secret(method_args)))
                    raise Exception("uuidcode={} - Unity communication failed".format(uuidcode))
                else:
                    app_logger.trace("uuidcode={} - Unity call successful".format(uuidcode))
                    return r.json()
        except:
            app_logger.exception("uuidcode={} - Unity communication failed".format(uuidcode))
