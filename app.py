import json
import pytz
import dateutil.parser

import flask
from flask import request
from flask_cors import CORS, cross_origin
import sqlite3

import maps

app = flask.Flask(__name__)
CORS(app)

optimization_data = None
optimization_cost = None

connection = sqlite3.connect('failures.db')
cursor = connection.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS failure ('
               'id INTEGER PRIMARY KEY, '
               'failure TEXT, '
               'before_cost REAL, '
               'after_cost REAL)')
connection.commit()
connection.close()


@app.route('/file', methods=['POST'])
@cross_origin()
def receive_file():
    global optimization_data, optimization_cost

    if 'file' not in request.files:
        return 'Invalid file', 400
    file = request.files['file'].stream

    string_content = file.read().decode('utf8').replace("'", '"')
    optimization_data = json.loads(string_content)

    optimization_cost, _ = maps.map_by_airplanes(optimization_data, 'Map1.html')

    return flask.jsonify(optimization_data), 200


@app.route('/map')
def home_endpoint():
    return flask.send_file('Map1.html')


@app.route('/failure', methods=['POST'])
@cross_origin()
def receive_failure():
    global optimization_data, optimization_cost

    failure = request.json

    failure_history = {
        'failure': str(failure['failure']),
        'before-cost': optimization_cost
    }

    failure_time = dateutil.parser.parse(failure['time'])
    airplane = list(filter(lambda airplane: airplane['tail'] == failure['airplane'], optimization_data['aeronaves']))[0]
    airplane['falhas'][str(failure['failure'])]\
        .append(failure_time.astimezone(pytz.timezone('America/Sao_Paulo')).strftime('%4Y-%m-%dT%H:%M:%S.%f'))

    optimization_cost, _ = maps.map_by_airplanes(optimization_data, 'Map1.html')
    failure_history['after-cost'] = optimization_cost
    __add_history_db(failure_history)

    return flask.jsonify(optimization_data), 200


def __add_history_db(failure_history):
    c = sqlite3.connect('failures.db')
    cur = c.cursor()
    cur.execute('INSERT INTO failure VALUES(NULL, ?, ?, ?)',
                (failure_history['failure'], failure_history['before-cost'], failure_history['after-cost']))
    c.commit()
    c.close()


@app.route('/failure/history', methods=['GET'])
@cross_origin()
def get_failure_history():
    c = sqlite3.connect('failures.db')
    cur = c.cursor()
    cur.execute('SELECT * FROM failure')
    failures = cur.fetchall()
    c.close()

    result = []
    for f_id, failure, before, after in failures:
        result.append({
            'id': f_id,
            'failure': failure,
            'before-cost': before,
            'after-cost': after
        })

    return flask.jsonify(result), 200


@app.route('/export', methods=['GET'])
@cross_origin()
def export_state():
    if optimization_data is None:
        return 'Empty data', 204
    return flask.jsonify(optimization_data), 200


if __name__ == '__main__':
    app.run(debug=True)
