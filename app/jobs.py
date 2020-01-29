'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

from flask import request
from flask_restful import Resource
from flask import current_app as app
from threading import Thread

from app import utils_common, jobs_threads_worker
from app import jobs_threads

class JobHandler(Resource):
    def get(self):
        try:
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("uuidcode={} - Get Server Status".format(uuidcode))
            app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers.to_list()))
    
            # Check for the J4J intern token
            utils_common.validate_auth(app.log,
                                       uuidcode,
                                       request.headers.get('intern-authorization', None))
    
            request_headers = {}
            for key, value in request.headers.items():
                if 'Token' in key: # refresh, jhub, access
                    key = key.replace('-', '_')
                request_headers[key.lower()] = value
            if not request_headers.get('tokenurl', None):
                request_headers['tokenurl'] = "https://unity-jsc.fz-juelich.de/jupyter-oauth2/token"
            if not request_headers.get('authorizeurl', None):
                request_headers['authorizeurl'] = "https://unity-jsc.fz-juelich.de/jupyter-oauth2-as/oauth2-authz"
            app.log.debug("uuidcode={} - Start Thread to communicate with worker".format(uuidcode))
            t = Thread(target=jobs_threads.get,
                       args=(app.log,
                             uuidcode,
                             request_headers,
                             app.urls,
                             app.database))
            t.start()
        except:
            app.log.exception("Jobs.get failed. Bugfix required")
        return '', 202

    def post(self):
        try:
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("uuidcode={} - Spawn Server".format(uuidcode))
            app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers.to_list()))
            app.log.trace("uuidcode={} - Json: {}".format(uuidcode, request.json))
    
            # Check for the J4J intern token
            utils_common.validate_auth(app.log,
                                       uuidcode,
                                       request.headers.get('intern-authorization', None))
    
            app.log.debug("uuidcode={} - Start Thread to communicate with worker".format(uuidcode))
            request_headers = {}
            for key, value in request.headers.items():
                if 'Token' in key: # refresh, jhub, access
                    key = key.replace('-', '_')
                request_headers[key.lower()] = value
            if not request_headers.get('tokenurl', None):
                request_headers['tokenurl'] = "https://unity-jsc.fz-juelich.de/jupyter-oauth2/token"
            if not request_headers.get('authorizeurl', None):
                request_headers['authorizeurl'] = "https://unity-jsc.fz-juelich.de/jupyter-oauth2-as/oauth2-authz"
            request_json = {}
            for key, value in request.json.items():
                if 'Token' in key: # refresh, jhub, access
                    key = key.replace('-', '_')
                request_json[key] = value
            if 'port' not in request_json.keys():
                # Find a random port, that's not already used by Jupyter@JSC
                request_json['port'] = jobs_threads_worker.random_port(app.log,
                                                                       uuidcode,
                                                                       app.database,
                                                                       app.database_tunnel)
                
                if request_json['port'] == 0:
                    return  '{}'.format(request_json['port']), 539
            app.log.trace("uuidcode={} - New Headers: {}".format(uuidcode, request_headers))
            app.log.trace("uuidcode={} - New Json: {}".format(uuidcode, request_json))
            t = Thread(target=jobs_threads.post,
                       args=(app.log,
                             uuidcode,
                             request_headers,
                             request_json,
                             app.urls,
                             app.database))
            t.start()
        except:
            app.log.exception("Jobs.post failed. Bugfix required")
        return '{}'.format(request_json['port']), 202

    def delete(self):
        try:
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("uuidcode={} - Delete Server".format(uuidcode))
            app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers.to_list()))
    
            # Check for the J4J intern token
            utils_common.validate_auth(app.log,
                                       uuidcode,
                                       request.headers.get('intern-authorization', None))
            request_headers = {}
            for key, value in request.headers.items():
                if 'Token' in key: # refresh, jhub, access
                    key = key.replace('-', '_')
                request_headers[key.lower()] = value
            if not request_headers.get('tokenurl', None):
                request_headers['tokenurl'] = "https://unity-jsc.fz-juelich.de/jupyter-oauth2/token"
            if not request_headers.get('authorizeurl', None):
                request_headers['authorizeurl'] = "https://unity-jsc.fz-juelich.de/jupyter-oauth2-as/oauth2-authz"
            app.log.debug("uuidcode={} - Start Delete Thread".format(uuidcode))
            t = Thread(target=jobs_threads.delete,
                       args=(app.log,
                             uuidcode,
                             request_headers,
                             app.urls,
                             app.database))
            t.start()
        except:
            app.log.exception("Jobs.delete failed. Bugfix required")
        return '', 202
