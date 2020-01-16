'''
Created on Jan 07, 2020

@author: Tim Kreuzer
'''

import json

from flask import request
from flask_restful import Resource
from flask import current_app as app

from app import utils_common
from app import utils_db


# With this class we can change the value of the column "skip" in the database, for a specific servername.
class SkipHandler(Resource):
    def post(self):
        try:
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("{} - Set skip".format(uuidcode))
            app.log.trace("{} - Headers: {}".format(uuidcode, request.headers.to_list()))
            app.log.trace("{} - Json: {}".format(uuidcode, json.dumps(request.json)))
    
            # Check for the J4J intern token
            utils_common.validate_auth(app.log,
                                       uuidcode,
                                       request.headers.get('intern-authorization', None))
            if request.json.get('value') and request.json.get('servername'):
                utils_db.set_skip(app.log,
                                  uuidcode,
                                  request.json.get('servername'),
                                  app.database,
                                  request.json.get('value'))
                return '', 202
            return '', 422
        except:
            app.log.exception("SkipHandler.post failed. Bugfix required")
            return '', 500
