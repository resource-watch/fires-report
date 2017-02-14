import os
import json
import csv
import StringIO
import logging
import datetime

from flask import jsonify, request
import requests

from . import endpoints
from firesreport.responders import ErrorResponder
from firesreport.utils.http import request_to_microservice, request_to_url


@endpoints.route('/firesreport', methods=['GET'])
def do_reports():
    '''Do Fires Report'''
    logging.info('Doing fires report')

    islands = request.args.get('islands', None)
    provinces = request.args.get('provinces', None)
    period = request.args.get('period', None)

    if (not islands and not provinces) or not period:
        return jsonify({'errors': [{
            'status': '400',
            'title': 'Islands or provinces (and period) should be set'
            }]
        }), 400

    if len(period.split(',')) < 2:
        return jsonify({'errors': [{
            'status': '400',
            'title': 'Period needs 2 arguments'
            }]
        }), 400

    period_from = period.split(',')[0]
    period_to = period.split(',')[1]

    try:
        datetime.datetime.strptime(period_from, '%Y-%m-%d')
        datetime.datetime.strptime(period_to, '%Y-%m-%d')
    except ValueError:
        return jsonify({'errors': [{
            'status': '400',
            'title': 'Not valid dates'
            }]
        }), 400

    if islands:
        column = 'ISLAND'
        values = islands.split(',')
    else:
        column = 'PROVINCE'
        values = provinces.split(',')

    values = "'"+ "','".join(values)+"'"

    payload = {
        'f': 'json',
        'spatialRelationship': 'esriSpatialRelIntersects',
        'outStatistics': "[{'onStatisticField':'ACQ_DATE','outStatisticFieldName':'Count','statisticType':'count'}]",
        'returnGeometry': False,
        'where': column +' in ('+values+') AND ACQ_DATE >= date\''+ period_from +'\' AND ACQ_DATE <= date\'' + period_to + '\'',
        'groupByFieldsForStatistics': ['ACQ_DATE'],
        'orderByFields': ['ACQ_DATE ASC']
    }

    try:
        response = requests.get('http://gis-potico.wri.org/arcgis/rest/services/Fires/FIRMS_ASEAN/MapServer/0/query', params=payload)
    except Error:
        return jsonify({'errors': [{
            'status': '500',
            'title': 'Service unavailable'
            }]
        }), 500

    response = response.json()
    r = {
        'id': None,
        'type': 'fires',
        'attributes': response.get('features')
    }

    return jsonify(r), 200
