'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

from flask import request
from flask_restful import Resource
from flask import current_app as app

from app import utils_common
from app import utils_db

# delete server from database
class DatabaseHandler(Resource):
    def delete(self):
        # Track actions through different webservices.
        uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
        app.log.info("uuidcode={} - Delete Database entry".format(uuidcode))
        app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers.to_list()))

        # Check for the J4J intern token
        utils_common.validate_auth(app.log,
                                   uuidcode,
                                   request.headers.get('intern-authorization', None))
        
        if request.headers.get('servername'):
            servername = request.headers.get('servername')
            infos = utils_db.get_entry_infos(app.log,
                                             uuidcode,
                                             servername,
                                             app.database)
            if len(infos) == 0:
                return '', 204
            utils_db.remove_entrys(app.log,
                                   uuidcode,
                                   servername,
                                   app.database)
            return '', 200
        return '', 422
