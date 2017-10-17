import flask

import maps

app = flask.Flask(__name__)


@app.route('/map')
def home_endpoint():
    return flask.send_file('Map1.html')


def main():
    maps.map_by_airplanes('Map1.html')


main()

if __name__ == '__main__':
    app.run(debug=True)
