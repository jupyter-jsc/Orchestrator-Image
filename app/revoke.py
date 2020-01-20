'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

import app.jobs_threads as jt
import json
import ast

from threading import Thread
from flask import request
from flask_restful import Resource
from flask import current_app as app

from app.utils_common import validate_auth
from app.utils_file_loads import get_unity
from app.utils_unity import communicate
from app.utils_db import get_all_servernames

class RevokeToken(Resource):
    def post_thread(self, app_logger, uuidcode, request_headers, request_json, app_urls, app_database):
        try:
            app_logger.trace("{} - Revoke Post_Thread start".format(uuidcode))
            if request_headers.get('stopall', 'false').lower() == 'true':
                # Try to stop all servers of the user. (For example if he logs out)
                if not request_headers.get('username'):
                    app_logger.error("{} - Could not stop all server of user. Key username not in header".format(uuidcode))
                else:
                    servernames = get_all_servernames(app_logger,
                                                      uuidcode,
                                                      request_headers.get('username'),
                                                      app_database)
                    delete_header = {
                                    'uuidcode': uuidcode,
                                    'accesstoken': request_json['accesstoken'],
                                    'refreshtoken': request_json['refreshtoken'],
                                    'expire': request_headers['expire'],
                                    'tokenurl': request_headers['tokenurl'],
                                    'authorizeurl': request_headers['authorizeurl'],
                                    'escapedusername': request_headers['escapedusername']
                                    }
                    for server in servernames:
                        delete_header['servername'] = server
                        app_logger.debug("{} - Delete server {}".format(uuidcode, server))
                        del_resp = jt.delete(app_logger,
                                             uuidcode,
                                             delete_header,
                                             app_urls,
                                             app_database)
                        app_logger.trace("{} - Delete server response {}".format(uuidcode, del_resp))
    
            app_logger.trace("{} - Call utils_file_loads.get_unity()".format(uuidcode))
            unity_file = get_unity()
            token_url = request_headers.get('tokenurl', '')
            revoke_url = unity_file[token_url]['links']['revoke']
            admin_tokens = unity_file[token_url]['links']['admin_tokens']
            admin_basic_token = unity_file[token_url]['admin_basic_token']
            cert = unity_file[token_url].get('certificate', False)
            immune_tokens = unity_file[token_url].get('immune_tokens', [])
            client_id = unity_file[token_url]['client_id']
    
            # Revoke all tokens, but these we just sent in the header. Useful when the users logs in. So old tokens will be removed
            if request_headers.get('allbutthese', 'false').lower() == 'true':
                username = 'UID={}'.format(request_headers.get('username'))
                headers = { 'Content-Type': 'application/json',
                            'Authorization': 'Basic {}'.format(admin_basic_token) }
                method_args = {"url": admin_tokens,
                               "headers": headers,
                               "certificate": cert}
                all_tokens_list = communicate(app_logger,
                                              uuidcode,
                                              "GET",
                                              method_args)
                immune_tokens.append(request_json['accesstoken'])
                immune_tokens.append(request_json['refreshtoken'])
                to_revoke_list = [x for x in all_tokens_list if json.loads(x.get('contents', {}).get('userInfo', "{}")).get('x500name') == username and x.get('value', '') not in immune_tokens]
                headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
                method_args = {"url": revoke_url,
                               "headers": headers,
                               "data": {"client_id": client_id,
                                        "logout": 'false'},
                               "certificate": cert}
                for token_dict in to_revoke_list:
                    token_type = token_dict.get('type', 'oauth2Access')
                    if token_type == 'oauth2Access':
                        token_type = 'access_token'
                    elif token_type == 'oauth2Refresh':
                        token_type = 'refresh_token'
                    else:
                        app_logger.trace("{} - Token_Dict: {}".format(uuidcode, token_dict))
                        app_logger.error("{} - Could not revoke token".format(uuidcode))
                        continue
                    token = token_dict.get('value', '')
                    app_logger.trace("{} - Revoke {} {}".format(uuidcode, token_type, token))
                    method_args['data']['token_type_hint'] = token_type
                    method_args['data']['token'] = token
                    communicate(app_logger,
                                uuidcode,
                                "POST",
                                method_args)
            else:
                headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
                tokens = {'access_token': request_json['accesstoken'],
                          'refresh_token': request_json['refreshtoken']}
                method_args = {"url": revoke_url,
                               "headers": headers,
                               "data": {"client_id": client_id,
                                        "logout": 'true'},
                               "certificate": cert}
                app_logger.debug("{} - Unity communication to revoke token.".format(uuidcode))
                for key, value in tokens.items():
                    method_args['data']['token_type_hint'] = key
                    method_args['data']['token'] = value
                    communicate(app_logger,
                                uuidcode,
                                "POST",
                                method_args)
        except:
            app_logger.exception("Revoke.post_thread failed. Bugfix required")

    def post(self):
        try:
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("{} - Revoke Token".format(uuidcode))
            app.log.trace("{} - Headers: {}".format(uuidcode, request.headers.to_list()))
            app.log.trace("{} - Json: {}".format(uuidcode, request.json))
            validate_auth(app.log,
                          uuidcode,
                          request.headers.get('intern-authorization', None))
            request_json = {}
            for key, value in request.json.items():
                request_json[key] = value
            request_headers = {}
            for key, value in request.headers.items():
                if 'Token' in key: # refresh, jhub, access
                    key = key.replace('-', '_')
                request_headers[key.lower()] = value
            t = Thread(target=self.post_thread,
                       args=(app.log,
                             uuidcode,
                             request_headers,
                             request_json,
                             app.urls,
                             app.database))
            t.start()
            return '', 202
        except:
            app.log.exception("Revoke.post failed. Bugfix required")
            return '', 500
