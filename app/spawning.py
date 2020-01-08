'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

import json

from flask import request
from flask_restful import Resource
from flask import current_app as app

from app import utils_common
from app import utils_db


# With this class we can change the value of the column "spawning" in the database, for a specific servername.
# If J4J_Worker is done with starting the JupyterLab, it will call this endpoint to tell J4J_Orchestrator, that the JupyterLab is running.
# Otherwise J4J_Orchestrator would ask J4J_Worker in another thread, if the JupyterLab is running. If this is not the case (because the start
# is not finished yet) the starting process would be canceled 
class SpawningHandler(Resource):
    def post(self):
        try:
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("{} - Set Spawning".format(uuidcode))
            app.log.trace("{} - Headers: {}".format(uuidcode, request.headers.to_list()))
            app.log.trace("{} - Json: {}".format(uuidcode, json.dumps(request.json)))
    
            # Check for the J4J intern token
            utils_common.validate_auth(app.log,
                                       uuidcode,
                                       request.headers.get('intern-authorization', None))
            if request.json.get('value') and request.json.get('servername'):
                utils_db.set_spawning(app.log,
                                      uuidcode,
                                      request.json.get('servername'),
                                      app.database,
                                      request.json.get('value'))
                return '', 202
            return '', 422
        except:
            app.log.error("SpawningHandler.post failed. Bugfix required")
            return '', 500
