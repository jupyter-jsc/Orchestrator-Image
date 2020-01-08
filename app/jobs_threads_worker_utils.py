'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

import requests
import traceback

from contextlib import closing

from app.utils_file_loads import get_j4j_worker_token
from app.utils_unity import renew_token

def create_get_header(app_logger, uuidcode, request_headers, app_hub_url_proxy_route, app_hub_token_url, username, servername, app_database):
    app_logger.trace("{} - Create J4J_Worker_Get_Header".format(uuidcode))
    accesstoken, expire = renew_token(app_logger,
                                      uuidcode,
                                      request_headers.get("tokenurl", "https://unity-jsc.fz-juelich.de/jupyter-oauth2/token"),
                                      request_headers.get("authorizeurl", "https://unity-jsc.fz-juelich.de/jupyter-oauth2-as/oauth2-authz"),
                                      request_headers.get("refreshtoken"),
                                      request_headers.get('accesstoken'),
                                      request_headers.get('expire'),
                                      request_headers.get('jhubtoken'),
                                      app_hub_url_proxy_route,
                                      app_hub_token_url,
                                      username,
                                      servername,
                                      app_database)
    worker_header = {"uuidcode": uuidcode,
                     "servername": request_headers.get('servername'),
                     "intern-authorization": get_j4j_worker_token(),
                     "expire": str(expire),
                     "refreshtoken": request_headers.get("refreshtoken"),
                     "accesstoken": accesstoken,
                     "tokenurl": request_headers.get("tokenurl", "https://unity-jsc.fz-juelich.de/jupyter-oauth2/token"),
                     "authorizeurl": request_headers.get("authorizeurl", "https://unity-jsc.fz-juelich.de/jupyter-oauth2-as/oauth2-authz"),
                     "escapedusername": username }
    return worker_header


def create_header(app_logger, uuidcode, request_headers, app_hub_url_proxy_route, app_hub_token_url, username, servername, app_database):
    app_logger.trace("{} - Create J4J_Worker_Header".format(uuidcode))
    accesstoken, expire = renew_token(app_logger,
                                      uuidcode,
                                      request_headers.get("tokenurl", "https://unity-jsc.fz-juelich.de/jupyter-oauth2/token"),
                                      request_headers.get("authorizeurl", "https://unity-jsc.fz-juelich.de/jupyter-oauth2-as/oauth2-authz"),
                                      request_headers.get("refreshtoken"),
                                      request_headers.get('accesstoken'),
                                      request_headers.get('expire'),
                                      request_headers.get('jhubtoken'),
                                      app_hub_url_proxy_route,
                                      app_hub_token_url,
                                      username,
                                      servername,
                                      app_database)

    j4j_worker_header = {"uuidcode": uuidcode,
                         "servername": request_headers.get('servername'),
                         "Intern-Authorization": get_j4j_worker_token(),
                         "expire": str(expire),
                         "refreshtoken": request_headers.get("refreshtoken"),
                         "jhubtoken": request_headers.get("jhubtoken"),
                         "accesstoken": accesstoken,
                         "escapedusername": username,
                         "tokenurl": request_headers.get("tokenurl", "https://unity-jsc.fz-juelich.de/jupyter-oauth2/token"),
                         "authorizeurl": request_headers.get("authorizeurl", "https://unity-jsc.fz-juelich.de/jupyter-oauth2-as/oauth2-authz"),
                         "account": request_headers.get("account"),
                         "project": request_headers.get("project")}
    return j4j_worker_header

def create_json(app_logger, uuidcode, request_json):
    app_logger.trace("{} - Create J4J_Worker_Json".format(uuidcode))
    j4j_worker_json = {
        "Environment": request_json.get("Environment", {}).copy(),
        "partition": request_json.get("partition"),
        "reservation": request_json.get("reservation"),
        "Resources": request_json.get("Resources", {}).copy(),
        "system": request_json.get("system"),
        "Checkboxes": request_json.get("Checkboxes", []).copy(),
        "port": request_json.get("port")
        }
    return j4j_worker_json

def communicate(app_logger, uuidcode, method, method_args):
    app_logger.debug("{} - J4J_Worker communication. {} {}".format(uuidcode, method_args.get('url', '<no url>'), method))
    app_logger.trace("{} - J4J_Worker communication. Method_args: {}".format(uuidcode, method_args))
    if method == "DELETE":
        with closing(requests.delete(method_args['url'],
                                     headers = method_args.get('headers', {}),
                                     json = method_args.get('json', {}),
                                     verify = method_args.get('certificate', False))) as r:
            app_logger.trace("{} - J4J_Worker communication response: {} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
            return r.text, r.status_code, r.headers
    elif method == "POST":
        with closing(requests.post(method_args['url'],
                                   headers = method_args.get('headers', {}),
                                   json = method_args.get('json', {}),
                                   verify = method_args.get('certificate', False))) as r:
            app_logger.trace("{} - J4J_Worker communication response: {} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
            return r.text, r.status_code, r.headers
    elif method == "GET":
        if method_args.get('fire_and_forget', False):
            try:
                with closing(requests.get(method_args['url'],
                                          headers = method_args.get('headers', {}),
                                          verify = method_args.get('certificate', False),
                                          timeout=0.5)) as r:
                    pass
            except requests.exceptions.ReadTimeout:
                pass
            except requests.exceptions.ConnectTimeout:
                app_logger.debug("{} - DEBUG: ConnectTimeout: {}".format(uuidcode, traceback.format_exc()))
                pass
