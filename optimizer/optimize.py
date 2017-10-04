import datetime


def optimize(airports):
    result = list()
    result.append({
        'airplane': 'TN001',
        'origin': (airports[0]['lat'], airports[0]['lon']),
        'destine': (airports[1]['lat'], airports[1]['lon']),
        'departure_time': datetime.datetime.now()
    })
    result.append({
        'airplane': 'TN002',
        'origin': (airports[2]['lat'], airports[2]['lon']),
        'destine': (airports[3]['lat'], airports[3]['lon']),
        'departure_time': datetime.datetime.now()
    })
    return result
