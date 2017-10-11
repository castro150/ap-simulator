import datetime


def get_routes(airports):
    routes = list()
    routes.append({
        'airplane': 'TN001',
        'origin': {
            'name': airports[0]['iata'],
            'lat': airports[0]['lat'],
            'lon': airports[0]['lon']
        },
        'destine': {
            'name': airports[1]['iata'],
            'lat': airports[1]['lat'],
            'lon': airports[1]['lon']
        },
        'departure_time': datetime.datetime.now()
    })
    routes.append({
        'airplane': 'TN002',
        'origin': {
            'name': airports[2]['iata'],
            'lat': airports[2]['lat'],
            'lon': airports[2]['lon']
        },
        'destine': {
            'name': airports[3]['iata'],
            'lat': airports[3]['lat'],
            'lon': airports[3]['lon']
        },
        'departure_time': datetime.datetime.now()
    })
    routes.append({
        'airplane': 'TN003',
        'origin': {
            'name': airports[3]['iata'],
            'lat': airports[3]['lat'],
            'lon': airports[3]['lon']
        },
        'destine': {
            'name': airports[7]['iata'],
            'lat': airports[7]['lat'],
            'lon': airports[7]['lon']
        },
        'departure_time': datetime.datetime.now()
    })
    routes.append({
        'airplane': 'TN002',
        'origin': {
            'name': airports[5]['iata'],
            'lat': airports[5]['lat'],
            'lon': airports[5]['lon']
        },
        'destine': {
            'name': airports[6]['iata'],
            'lat': airports[6]['lat'],
            'lon': airports[6]['lon']
        },
        'departure_time': datetime.datetime.now()
    })
    return routes
