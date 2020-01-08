'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

from flask import abort

from app.utils_file_loads import get_j4j_orchestrator_token

def validate_auth(app_logger, uuidcode, intern_authorization):
    if not intern_authorization == None:
        token = get_j4j_orchestrator_token()
        if intern_authorization == token:
            app_logger.debug("{} - intern-authorization validated".format(uuidcode))
            return
    app_logger.warning("{} - Could not validate Intern-Authorization".format(uuidcode))
    abort(401)

def remove_secret(json_dict):
    if type(json_dict) != dict:
        return json_dict
    secret_dict = {}
    for key, value in json_dict.items():
        if type(value) == dict:
            secret_dict[key] = remove_secret(value)
        elif key.lower() in ["authorization", "accesstoken", "refreshtoken", "jhubtoken", "intern-authorization"]:
            secret_dict[key] = '<secret>'
        else:
            secret_dict[key] = value
    return secret_dict
