'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

import requests
import json
from contextlib import closing

from app.utils_file_loads import get_jhubtoken
from app.utils_common import remove_secret

# If we receive a 503 from a JupyterHub call it means, the host, where the route leads to, does not exist anymore. 
# So we try to reach any other running JupyterHub instance to remove the routings to this host.
def remove_proxy_route(app_logger, uuidcode, app_hub_url_proxy_route, jhubtoken, username, server_name):
    app_logger.debug("{} - Remove proxys from server_name, because the original host is not accessable any longer".format(uuidcode))
    hub_header = {"Authorization": "token {}".format(jhubtoken),
                  "uuidcode": uuidcode,
                  "Intern-Authorization": get_jhubtoken()}
    app_logger.info("{} - Remove Proxys for {}".format(uuidcode, server_name))
    url = app_hub_url_proxy_route
    try:
        if ':' in server_name:
            server_name = server_name.split(':')[1]
        url = url + '/' + username
        if server_name != '':
            url = url + '/' + server_name
        app_logger.trace("{} - Delete Proxy Route: {} {}".format(uuidcode, url, hub_header))
        for i in range(0, 10):
            with closing(requests.delete(url,
                                         headers = hub_header,
                                         verify = False,
                                         timeout = 10)) as r:
                if r.status_code == 200:
                    app_logger.info("{} - Proxy route deletion successful".format(uuidcode))
                    return True
                elif r.status_code == 503:
                    app_logger.info("{} - Proxy route deletion status_code 503. Try again (Try {}/10)".format(uuidcode, i+1))
                else:
                    raise Exception("{} - Could not remove proxy route for server_name {}: {} {}".format(uuidcode, server_name, r.text, r.status_code))
    except:
        app_logger.exception("{} - Could not remove route from proxy via JupyterHub".format(uuidcode))


def get_tokens(app_logger, uuidcode, app_hub_url_proxy_route, app_hub_token_url, jhubtoken, username, server_name):
    app_logger.info("{} - Get oauth tokens from JupyterHub".format(uuidcode))
    hub_header = {"Authorization": "token {}".format(jhubtoken),
                  "uuidcode": uuidcode,
                  "Intern-Authorization": get_jhubtoken()}
    try:
        app_logger.trace("{} - Header: {}".format(uuidcode, hub_header))
        url = app_hub_token_url
        if ':' in server_name:
            server_name = server_name.split(':')[1]
        url = url + '/' + username
        if server_name != '':
            url = url + '/' + server_name
        with closing(requests.get(url,
                                  headers = hub_header,
                                  verify = False,
                                  timeout = 10)) as r:
            if r.status_code == 201:
                app_logger.trace("{} - Token Get successful: {} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
                tokens_json = json.loads(r.text)
                return tokens_json.get('accesstoken'), tokens_json.get('refreshtoken'), tokens_json.get('expire')
            elif r.status_code == 503:
                app_logger.info("{} - Try to remove the proxys for the dead host".format(uuidcode))
                remove_proxy_route(app_logger,
                                   uuidcode,
                                   app_hub_url_proxy_route,
                                   jhubtoken,
                                   username,
                                   server_name)
                # try again
                with closing(requests.get(url,
                                          headers = hub_header,
                                          verify = False,
                                          timeout = 10)) as r2:
                    if r2.status_code == 201:
                        app_logger.trace("{} - Token Get successful: {} {} {}".format(uuidcode, r2.text, r2.status_code, r2.headers))
                        tokens_json = json.loads(r2.text)
                        return tokens_json.get('accesstoken'), tokens_json.get('refreshtoken'), tokens_json.get('expire')
                    else:
                        app_logger.error("{} - Token Get sent wrong status_code: {} {} {}".format(uuidcode, r2.text, r2.status_code, r2.headers))
            else:
                app_logger.error("{} - Token Get sent wrong status_code: {} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
    except:
        app_logger.exception("{} - Could not get token from JupyterHub".format(uuidcode))
    raise Exception("{} - Could not get token from JupyterHub".format(uuidcode))
        

def token(app_logger, uuidcode, app_hub_url_proxy_route, app_hub_token_url, jhubtoken, accesstoken, expire, username, server_name):
    app_logger.debug("{} - Send new token to JupyterHub".format(uuidcode))
    app_logger.trace("{} - Access-token: {} , expire: {}".format(uuidcode, accesstoken, expire))
    hub_header = {"Authorization": "token {}".format(jhubtoken),
                  "uuidcode": uuidcode,
                  "Intern-Authorization": get_jhubtoken()}
    hub_json = {"accesstoken": accesstoken,
                "expire": str(expire)}
    try:
        app_logger.info("{} - Update JupyterHub Token".format(uuidcode))
        app_logger.trace("{} - Header: {}".format(uuidcode, hub_header))
        app_logger.trace("{} - JSON: {}".format(uuidcode, hub_json))
        url = app_hub_token_url
        if ':' in server_name:
            server_name = server_name.split(':')[1]
        url = url + '/' + username
        if server_name != '':
            url = url + '/' + server_name
        with closing(requests.post(url,
                                   headers = hub_header,
                                   json = hub_json,
                                   verify = False,
                                   timeout = 10)) as r:
            if r.status_code == 201:
                app_logger.trace("{} - Token Update successful: {} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
                return
            elif r.status_code == 503:
                app_logger.info("{} - Try to remove the proxys for the dead host".format(uuidcode))
                remove_proxy_route(app_logger,
                                   uuidcode,
                                   app_hub_url_proxy_route,
                                   jhubtoken,
                                   username,
                                   server_name)
                # try again
                with closing(requests.post(url,
                                           headers = hub_header,
                                           json = hub_json,
                                           verify = False,
                                           timeout = 10)) as r2:
                    if r2.status_code == 201:
                        app_logger.trace("{} - Token Update successful: {} {} {}".format(uuidcode, r2.text, r2.status_code, r2.headers))
                        return
                    else:
                        app_logger.error("{} - Token Update sent wrong status_code: {} {} {}".format(uuidcode, r2.text, r2.status_code, r2.headers))
            else:
                app_logger.error("{} - Token Update sent wrong status_code: {} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
    except:
        app_logger.exception("{} - Could not send update token to JupyterHub".format(uuidcode))

def status(app_logger, uuidcode, app_hub_url_proxy_route, app_hub_update_url, jhubtoken, status, username, server_name):
    app_logger.debug("{} - Send job status to JupyterHub for servername {}: {}".format(uuidcode, server_name, status))
    hub_header = {"Authorization": "token {}".format(jhubtoken),
                  "uuidcode": uuidcode,
                  "Intern-Authorization": get_jhubtoken()}
    hub_json = { "Status": status }
    try:
        app_logger.info("{} - Update JupyterHub Status ({})".format(uuidcode, status))
        url = app_hub_update_url
        if ':' in server_name:
            server_name = server_name.split(':')[1]
        url = url + '/' + username
        if server_name != '':
            url = url + '/' + server_name
        with closing(requests.post(url,
                                   headers = hub_header,
                                   json = hub_json,
                                   verify = False,
                                   timeout = 10)) as r:
            if r.status_code == 201:
                app_logger.trace("{} - Status Update successful: {} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
                return
            elif r.status_code == 503:
                app_logger.info("{} - Try to remove the proxys for the dead host".format(uuidcode))
                remove_proxy_route(app_logger,
                                   uuidcode,
                                   app_hub_url_proxy_route,
                                   jhubtoken,
                                   username,
                                   server_name)
                # try again
                with closing(requests.post(url,
                                           headers = hub_header,
                                           json = hub_json,
                                           verify = False,
                                           timeout = 10)) as r2:
                    if r2.status_code == 201:
                        app_logger.trace("{} - Status Update successful: {} {} {}".format(uuidcode, r2.text, r2.status_code, r2.headers))
                        return
                    elif r2.status_code == 404:
                        app_logger.info("{} - JupyterHub doesn't know the spawner.".format(uuidcode))
            elif r.status_code == 404:
                app_logger.info("{} - JupyterHub doesn't know the spawner.".format(uuidcode))
            app_logger.warning("{} - JupyterHub.update sent wrong status_code: {} {} {}".format(uuidcode, r.text, r.status_code, remove_secret(r.headers)))
    except:
        app_logger.exception("{} - Could not send Status Update to JupyterHub".format(uuidcode))

def cancel(app_logger, uuidcode, app_hub_url_proxy_route, app_hub_cancel_url, jhubtoken, errormsg, username, server_name):
    app_logger.debug("{} - Send cancel to JupyterHub".format(uuidcode))
    hub_header = {"Authorization": "token {}".format(jhubtoken),
                  "Intern-Authorization": get_jhubtoken(),
                  "uuidcode": uuidcode,
                  "Error": errormsg,
                  "Stopped": "True"}
    try:
        app_logger.info("{} - Cancel JupyterHub Server".format(uuidcode))
        url = app_hub_cancel_url
        if ':' in server_name:
            server_name = server_name.split(':')[1]
        url = url + '/' + username
        if server_name != '':
            url = url + '/' + server_name
        with closing(requests.delete(url,
                                     headers = hub_header,
                                     verify = False,
                                     timeout = 10)) as r:
            if r.status_code == 202:
                app_logger.trace("{} - Cancel successful: {} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
                return
            elif r.status_code == 503:
                app_logger.info("{} - Try to remove the proxys for the dead host".format(uuidcode))
                remove_proxy_route(app_logger,
                                   uuidcode,
                                   app_hub_url_proxy_route,
                                   jhubtoken,
                                   username,
                                   server_name)
                # try again
                with closing(requests.delete(url,
                                             headers = hub_header,
                                             verify = False,
                                             timeout = 10)) as r2:
                    if r2.status_code == 202:
                        app_logger.trace("{} - Cancel successful: {} {} {}".format(uuidcode, r2.text, r2.status_code, r2.headers))
                        return
                    else:
                        app_logger.warning("{} - JupyterHub.cancel sent wrong status_code: {} {} {}".format(uuidcode, r2.text, r2.status_code, remove_secret(r2.headers)))
            else:
                app_logger.warning("{} - JupyterHub.cancel sent wrong status_code: {} {} {}".format(uuidcode, r.text, r.status_code, remove_secret(r.headers)))
    except:
        app_logger.exception("{} - Could not send cancel to JupyterHub".format(uuidcode))
