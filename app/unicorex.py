'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

import requests

from flask import request
from flask_restful import Resource
from flask import current_app as app
from contextlib import closing

from app import utils_common, utils_file_loads

class UNICOREXHandler(Resource):
    def get(self):
        try:
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("{} - Get UNICOREX User".format(uuidcode))
            app.log.trace("{} - Headers: {}".format(uuidcode, request.headers.to_list()))

            # Check for the J4J intern token
            utils_common.validate_auth(app.log,
                                       uuidcode,
                                       request.headers.get('intern-authorization', None))

            request_headers = {}
            for key, value in request.headers.items():
                if 'Token' in key: # refresh, jhub, access
                    key = key.replace('-', '_')
                request_headers[key.lower()] = value
            machines = request_headers.get('machines', '').split(' ')
            h = { "Accept": "application/json",
                  "User-Agent": request_headers.get('User-Agent'),
                  "Authorization": "Bearer {}".format(request_headers.get('accesstoken')) }
            unicore = utils_file_loads.get_unicore()
            xlogins = {}
            for machine in machines:
                url = unicore.get(machine, {}).get('link', '<no_url_found_for_{}>'.format(machine))
                cert = unicore.get(machine, {}).get('certificate', False)
                try:
                    with closing(requests.get(url,
                                              headers=h,
                                              verify=cert,
                                              timeout=1800)) as r:
                        if r.status_code == 200:
                            xlogins[machine] = r.json().get('client', {}).get('xlogin', {})
                            app.log.trace("{} - {} returned {}".format(uuidcode, machine, xlogins[machine]))
                        else:
                            app.log.warning("{} - Could not get user information from {}. {} {} {}".format(uuidcode, machine, r.status_code, r.text, r.headers))
                except requests.exceptions.ConnectTimeout:
                    app.log.exception("{} - Timeout (1800) reached".format(uuidcode))
                except:
                    app.log.exception("{} - Could not get user information from {}".format(uuidcode, machine))
            ret = {}
            resources = utils_file_loads.get_resources()
            for system, xlogin in xlogins.items():
                if system not in ret.keys():
                    ret[system] = {}
                # {'UID': 'di76bey', 'availableGroups': [], 'availableUIDs': ['di76bey']}
                for account in xlogin.get('availableUIDs', []):
                    if account == '!!DISCLAIMER!!':
                        continue
                    if account not in ret[system].keys():
                        ret[system][account] = {}
                    for group in xlogin.get('availableGroups', ["default"]):
                        if group not in ret[system][account].keys():
                            ret[system][account][group] = {}
                        for partition in resources.get(machine, {}).keys():
                            if partition not in ret[system][account][group].keys():
                                ret[system][account][group][partition] = {}
        except:
            app.log.exception("UNICORE/X get failed. Bugfix required")
            return '', 500
        return ret, 200

