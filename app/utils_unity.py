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
from app.utils_common import remove_secret
from app.utils_db import set_skip


def renew_token(app_logger, uuidcode, token_url, authorize_url, refreshtoken, accesstoken, expire, jhubtoken, app_hub_url_proxy_route, app_hub_token_url, username, servername, app_database):
    try:
        if int(expire) - time.time() > 480:
            return accesstoken, expire
    except:
        app_logger.warning("{} - Could not check if token will expire soon. Try to renew token.".format(uuidcode))
    app_logger.info("{} - Renew Token".format(uuidcode))
    unity = get_unity()
    if token_url == '':
        app_logger.warning("{} - Use default token_url. Please send token_url in header".format(uuidcode))
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
                app_logger.info("{} - Post to {}".format(uuidcode, token_url))
                app_logger.trace("{} - Header: {}".format(uuidcode, headers))
                app_logger.trace("{} - Data: {}".format(uuidcode, data))
                with closing(requests.post(token_url,
                                           headers = headers,
                                           data = data,
                                           verify = cert_path,
                                           timeout = 1800)) as r:
                    app_logger.trace("{} - Unity Response: {} {} {} {}".format(uuidcode, r.text, r.status_code, r.headers, r.json))
                    accesstoken = r.json().get('access_token')
                app_logger.info("{} - Get to {}".format(uuidcode, tokeninfo_url))
                with closing(requests.get(tokeninfo_url,
                                          headers = { 'Authorization': 'Bearer {}'.format(accesstoken) },
                                          verify = cert_path,
                                          timeout = 1800)) as r:
                    app_logger.trace("{} - Unity Response: {} {} {} {}".format(uuidcode, r.text, r.status_code, r.headers, r.json))
                    expire = r.json().get('exp')
                    break
            except:
                app_logger.warning("{} - Could not update token. This was the {}/10 try. {}".format(uuidcode, i+1, "Raise Exception" if i==9 else "Try again in 30 seconds"))
                if i==0:
                    app_logger.warning("{} - Set Skip to True for {}".format(uuidcode, servername))
                    set_skip(app_logger,
                             uuidcode,
                             servername,
                             app_database,
                             'True')
                    changed_skip = True
                if i==9:
                    raise Exception("{} - Tried 10 times".format(uuidcode))
                time.sleep(30)
    except:
        app_logger.warning("{} - Could not update token".format(uuidcode))
        raise Exception("{} - Could not update token".format(uuidcode))
    if changed_skip:
        app_logger.warning("{} - Set Skip to False for {}".format(uuidcode, servername))
        set_skip(app_logger,
                 uuidcode,
                 servername,
                 app_database,
                 'False')
    app_logger.debug("{} - Token renewed".format(uuidcode))
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
    app_logger.trace("{} - Start unity.communicate()".format(uuidcode))
    app_logger.trace("{} - Method: {} - Method_args: {}".format(uuidcode, method, method_args))
    if method == "POST":
        try:
            app_logger.info("{} - Post to {}".format(uuidcode, method_args.get('url', '<no_url>')))
            with closing(requests.post(method_args['url'],
                                       headers = method_args.get('headers', {}),
                                       data = method_args.get('data', "{}"),
                                       verify = method_args.get('certificate', False),
                                       timeout = 1800)) as r:
                if r.status_code != success_code:
                    app_logger.warning("{} - Unity communication response: {} {}".format(uuidcode, r.text, r.status_code))
                    app_logger.warning("{} - arguments: method_args: {}".format(uuidcode, remove_secret(method_args)))
                else:
                    app_logger.trace("{} - Unity call successful".format(uuidcode))
        except:
            app_logger.exception("{} - Unity communication failed".format(uuidcode))
    if method == "GET":
        try:
            app_logger.info("{} - Get to {}".format(uuidcode, method_args.get('url', '<no_url>')))
            with closing(requests.get(method_args['url'],
                                      headers = method_args.get('headers', {}),
                                      verify = method_args.get('certificate', False),
                                      timeout = 1800)) as r:
                if r.status_code != success_code:
                    app_logger.warning("{} - Unity communication response: {} {}".format(uuidcode, r.text, r.status_code))
                    app_logger.warning("{} - arguments: method_args: {}".format(uuidcode, remove_secret(method_args)))
                    raise Exception("{} - Unity communication failed".format(uuidcode))
                else:
                    app_logger.trace("{} - Unity call successful".format(uuidcode))
                    ret = {k: str(v).encode("utf-8") for k,v in r.json().items()}
                    return ret
        except:
            app_logger.exception("{} - Unity communication failed".format(uuidcode))
