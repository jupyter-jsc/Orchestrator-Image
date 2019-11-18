'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

from flask_restful import Resource

class HealthHandler(Resource):
    def get(self):
        return '', 200
