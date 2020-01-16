'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

import requests

from flask import request
from flask_restful import Resource
from flask import current_app as app
from contextlib import closing
from threading import Thread

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
            t = Thread(target=self.get_thread,
                       args=(app.log,
                             uuidcode,
                             request_headers,
                             app.urls,
                             app.database))
            t.start()
        except:
            app.log.exception("UNICORE/X get failed. Bugfix required")
            return '', 500
        return '', 204

    def get_thread(self, app_logger, uuidcode, request_headers, app_urls, app_database):
        try:
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
                for account in xlogin.get('availableUIDs', []):
                    if account == '!!DISCLAIMER!!':
                        continue
                    if account not in ret[system].keys():
                        ret[system][account] = {}
                    groups = xlogin.get('availableGroups', [])
                    if len(groups) == 0:
                        groups = ["default"]
                    for group in groups:
                        if group not in ret[system][account].keys():
                            ret[system][account][group] = {}
                        for partition in resources.get(machine, {}).keys():
                            if partition not in ret[system][account][group].keys():
                                ret[system][account][group][partition] = {}
            # send update to jhub
            url = app_urls.get('hub', {}).get('url_useraccs', '<No_url_found>')
            url = url.replace('<user>', request_headers.get('username'))
            hub_header = {'uuidcode': uuidcode,
                          'Intern-Authorization': get_jhubtoken()}
            hub_json = { 'useraccs': ret }
            with closing(requests.post(url,
                                       headers=hub_header,
                                       json=hub_json,
                                       verify=False,
                                       timeout=1800)) as r:
                if r.status_code == 204:
                    app_logger.trace("{} - User accs sent successfully:{} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
                elif r.status_code == 503:
                    app_logger.info("{} - Try to remove the proxys for the dead host".format(uuidcode))
                    remove_proxy_route(app_logger,
                                       uuidcode,
                                       app_urls.get('hub', {}).get('url_proxy_route', '<no_url_found>'),
                                       request_headers.get('jhubtoken'),
                                       request_headers.get('username'),
                                       '')
                    # try again
                    with closing(requests.post(url,
                                               headers = hub_header,
                                               json = hub_json,
                                               verify = False,
                                               timeout = 1800)) as r2:
                        if r2.status_code == 204:
                            app_logger.trace("{} - User accs sent successfully:{} {} {}".format(uuidcode, r2.text, r2.status_code, r2.headers))
                            return
                        else:
                            app_logger.error("{} - Useracc update sent wrong status_code: {} {} {}".format(uuidcode, r2.text, r2.status_code, r2.headers))
                else:
                    app_logger.error("{} - Usercc update sent wrong status_code: {} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
        except:
            app.log.exception("UNICORE/X get failed. Bugfix required")
            return '', 500
        return ret, 200

