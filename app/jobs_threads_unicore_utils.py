'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

import requests
import traceback

from contextlib import closing

from app.utils_file_loads import get_j4j_unicore_token
from app.utils_unity import renew_token

def create_get_header(app_logger, uuidcode, request_headers, app_hub_url_proxy_route, app_hub_token_url, username, servername, app_database):
    app_logger.trace("uuidcode={} - Create J4J_UNICORE_Get_Header".format(uuidcode))
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
    unicore_header = {"uuidcode": uuidcode,
                      "servername": request_headers.get('servername'),
                      "intern-authorization": get_j4j_unicore_token(),
                      "expire": str(expire),
                      "refreshtoken": request_headers.get("refreshtoken"),
                      "accesstoken": accesstoken,
                      "tokenurl": request_headers.get("tokenurl", "https://unity-jsc.fz-juelich.de/jupyter-oauth2/token"),
                      "authorizeurl": request_headers.get("authorizeurl", "https://unity-jsc.fz-juelich.de/jupyter-oauth2-as/oauth2-authz"),
                      "escapedusername": username }
    return unicore_header


def create_header(app_logger, uuidcode, request_headers, app_hub_url_proxy_route, app_hub_token_url, username, servername, app_database):
    app_logger.trace("uuidcode={} - Create J4J_UNICORE_Header".format(uuidcode))
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

    j4j_unicore_header = {"uuidcode": uuidcode,
                          "servername": request_headers.get('servername'),
                          "Intern-Authorization": get_j4j_unicore_token(),
                          "expire": str(expire),
                          "refreshtoken": request_headers.get("refreshtoken"),
                          "jhubtoken": request_headers.get("jhubtoken"),
                          "accesstoken": accesstoken,
                          "escapedusername": username,
                          "tokenurl": request_headers.get("tokenurl", "https://unity-jsc.fz-juelich.de/jupyter-oauth2/token"),
                          "authorizeurl": request_headers.get("authorizeurl", "https://unity-jsc.fz-juelich.de/jupyter-oauth2-as/oauth2-authz"),
                          "account": request_headers.get("account"),
                          "project": request_headers.get("project")}
    return j4j_unicore_header

def create_json(app_logger, uuidcode, request_json):
    app_logger.trace("uuidcode={} - Create J4J_UNICORE_Json".format(uuidcode))
    j4j_unicore_json = {"Environment": request_json.get("Environment", {}).copy(),
                        "partition": request_json.get("partition"),
                        "reservation": request_json.get("reservation"),
                        "Resources": request_json.get("Resources", {}).copy(),
                        "service": request_json.get("service"),
                        "dashboard": request_json.get('dashboard'),
                        "system": request_json.get("system"),
                        "Checkboxes": request_json.get("Checkboxes", {}).copy(),
                        "port": request_json.get("port")}
    return j4j_unicore_json

def communicate(app_logger, uuidcode, method, method_args):
    app_logger.debug("uuidcode={} - J4J_UNICORE communication. {} {}".format(uuidcode, method_args.get('url', '<no url>'), method))
    app_logger.trace("uuidcode={} - J4J_UNICORE communication. Method_args: {}".format(uuidcode, method_args))
    if method == "DELETE":
        try:
            with closing(requests.delete(method_args['url'],
                                         headers = method_args.get('headers', {}),
                                         json = method_args.get('json', {}),
                                         verify = method_args.get('certificate', False),
                                         timeout=1800)) as r:
                app_logger.trace("uuidcode={} - J4J_UNICORE communication response: {} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
                return r.text, r.status_code, r.headers
        except requests.exceptions.ConnectTimeout:
            app_logger.exception("uuidcode={} - Timeout (1800) reached".format(uuidcode))
            raise Exception("{} - Timeout".format(uuidcode))
    elif method == "POST":
        try:
            with closing(requests.post(method_args['url'],
                                       headers = method_args.get('headers', {}),
                                       json = method_args.get('json', {}),
                                       verify = method_args.get('certificate', False),
                                       timeout=21600)) as r:
                app_logger.trace("uuidcode={} - J4J_UNICORE communication response: {} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
                return r.text, r.status_code, r.headers
        except requests.exceptions.ConnectTimeout:
            app_logger.exception("uuidcode={} - Timeout (21600) reached".format(uuidcode))
            raise Exception("uuidcode={} - Timeout".format(uuidcode))
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
                app_logger.debug("uuidcode={} - DEBUG: ConnectTimeout: {}".format(uuidcode, traceback.format_exc()))
                pass
