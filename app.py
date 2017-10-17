import json
import flask
from flask import request
from flask_cors import CORS, cross_origin

import maps

app = flask.Flask(__name__)
CORS(app)


@app.route('/file', methods=['POST'])
@cross_origin()
def receive_file():
    if 'file' not in request.files:
        return 'Invalid file', 400
    file = request.files['file'].stream

    string_content = file.read().decode('utf8').replace("'", '"')
    data = json.loads(string_content)
    print(data)

    maps.map_by_airplanes('Map1.html')

    return 'Optimized', 200


@app.route('/map')
def home_endpoint():
    return flask.send_file('Map1.html')


if __name__ == '__main__':
    app.run(debug=True)
